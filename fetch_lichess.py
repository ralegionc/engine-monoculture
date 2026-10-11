"""Sample games from every Lichess monthly dump without downloading the dumps.

A recent dump is ~30 GB of zstd, but it is written as many independent zstd
frames, and the server honours HTTP Range requests. So for each month we cut
the file into K equal strata, read one CHUNK-sized slice at a random offset in
each, start decoding at the first frame header inside the slice, and keep
every complete game. Games in a dump are in time order, so the strata spread
the sample across the whole month instead of its first day.

Output: data/lichess/YYYY-MM.parquet, one row per game (date, speed, ratings,
first 20 plies). Months already written are skipped, so the run resumes.

Usage:  python fetch_lichess.py [--start 2013-01] [--end 2026-09] [--k 20] [--chunk-mb 5] [--jobs 3]
"""
import argparse
import io
import os
import random
import re
import sys
import time
import urllib.request
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd
import zstandard

from common import DATA, UA, lichess_speed, san_plies

URL = "https://database.lichess.org/standard/lichess_db_standard_rated_{m}.pgn.zst"
OUTDIR = os.path.join(DATA, "lichess")
MAGIC = b"\x28\xb5\x2f\xfd"
TAG = re.compile(r'^\[(\w+) "(.*)"\]$', re.M)
KEEP_TAGS = {"Event", "UTCDate", "WhiteElo", "BlackElo", "TimeControl", "Termination", "Result"}


def http_get(url, start=None, end=None, tries=5):
    headers = {"User-Agent": UA}
    if start is not None:
        headers["Range"] = "bytes={}-{}".format(start, end)
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120).read()
        except Exception as e:  # network hiccups: back off and retry
            if i == tries - 1:
                raise
            time.sleep(5 * (i + 1))


def file_size(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    return int(urllib.request.urlopen(req, timeout=60).headers["Content-Length"])


def decode_slice(buf, from_start=False):
    """Decompress whole and partial frames in buf, starting at the first real frame."""
    dctx = zstandard.ZstdDecompressor()
    pos = 0 if from_start else buf.find(MAGIC)
    while pos != -1:
        out = []
        reader = dctx.stream_reader(io.BytesIO(buf[pos:]), read_across_frames=True)
        try:
            while True:
                c = reader.read(1 << 20)
                if not c:
                    break
                out.append(c)
        except zstandard.ZstdError:
            pass  # a false magic fails at once; the truncated last frame fails at the end
        if sum(map(len, out)) > 4096:
            return b"".join(out).decode("utf-8", "replace")
        pos = buf.find(MAGIC, pos + 1)
    return ""


def split_games(text, whole_file=False):
    """Complete games in a decoded slice: drop the partial first and last game."""
    i = 0 if (whole_file and text.startswith("[Event ")) else text.find("\n[Event ")
    if i == -1:
        return []
    j = len(text) if whole_file else text.rfind("\n[Event ")
    body = text[i:j]
    return [g for g in body.split("\n[Event ") if g.strip()]


def parse_game(g):
    head, _, moves = g.partition("\n\n")
    if not g.startswith("[Event "):
        g = "[Event " + g
        head, _, moves = g.partition("\n\n")
    h = {k: v for k, v in TAG.findall(head) if k in KEEP_TAGS}
    moves = moves.strip()
    if not moves:
        return None
    plies = san_plies(moves[:2500])
    if len(plies) < 20 and len(moves) > 2500:
        plies = san_plies(moves)
    try:
        we, be = int(h.get("WhiteElo", "")), int(h.get("BlackElo", ""))
    except ValueError:
        return None
    return (h.get("UTCDate", "").replace(".", "-"), lichess_speed(h.get("TimeControl")),
            h.get("TimeControl", ""), we, be, h.get("Result", ""), h.get("Termination", ""),
            len(plies), " ".join(plies))


COLS = ["date", "speed", "tc", "welo", "belo", "result", "term", "nply", "moves"]


def sample_month(month, k, chunk):
    out = os.path.join(OUTDIR, month + ".parquet")
    if os.path.exists(out):
        return month, -1, 0, 0.0
    t0 = time.time()
    url = URL.format(m=month)
    size = file_size(url)
    rows, read = [], 0
    if size <= k * chunk:
        buf = http_get(url)
        read = len(buf)
        texts = [(decode_slice(buf, from_start=True), True)]
    else:
        rng = random.Random(month)
        stratum = size // k
        texts = []
        for s in range(k):
            off = s * stratum + rng.randrange(0, max(1, stratum - chunk))
            buf = http_get(url, off, off + chunk - 1)
            read += len(buf)
            texts.append((decode_slice(buf), False))
    for text, whole in texts:
        for g in split_games(text, whole_file=whole):
            r = parse_game(g)
            if r:
                rows.append(r)
    df = pd.DataFrame(rows, columns=COLS)
    df.insert(0, "month", month)
    df.to_parquet(out + ".part", index=False, engine="pyarrow")
    os.replace(out + ".part", out)
    return month, len(df), read, time.time() - t0


def months(start, end):
    y, m = map(int, start.split("-"))
    ye, me = map(int, end.split("-"))
    while (y, m) <= (ye, me):
        yield "{:04d}-{:02d}".format(y, m)
        m += 1
        if m == 13:
            y, m = y + 1, 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2013-01")
    ap.add_argument("--end", default="2026-09")
    ap.add_argument("--k", type=int, default=20, help="strata (slices) per month")
    ap.add_argument("--chunk-mb", type=float, default=5.0)
    ap.add_argument("--jobs", type=int, default=3)
    args = ap.parse_args()
    os.makedirs(OUTDIR, exist_ok=True)
    chunk = int(args.chunk_mb * 1024 * 1024)
    todo = list(months(args.start, args.end))
    with ProcessPoolExecutor(args.jobs) as ex:
        futs = [ex.submit(sample_month, m, args.k, chunk) for m in todo]
        for f in as_completed(futs):
            m, n, read, dt = f.result()
            if n >= 0:
                print("{}  {:9,d} games  {:6.0f} MB  {:5.0f}s".format(m, n, read / 1e6, dt), flush=True)


if __name__ == "__main__":
    sys.exit(main())
