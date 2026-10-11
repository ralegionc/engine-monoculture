"""Download The Week in Chess PGN archives and keep each game's opening.

Issues 920 (June 2012) onward ship as twicNNNNg.zip. Zips are cached in
data/raw/twic so the parse can be rerun offline. Output: data/twic.parquet,
one row per game with date, ratings, event class and the first 20 plies.

Usage:  python fetch_twic.py [--first 920] [--last 0]
"""
import argparse
import io
import os
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile

import pandas as pd

from common import DATA, PLIES, UA, san_plies, twic_kind

URL = "https://theweekinchess.com/zips/twic{n}g.zip"
RAW = os.path.join(DATA, "raw", "twic")
TAG = re.compile(r'^\[(\w+) "(.*)"\]\s*$')


def download(n):
    path = os.path.join(RAW, "twic{}g.zip".format(n))
    if os.path.exists(path):
        return path
    req = urllib.request.Request(URL.format(n=n), headers={
        "User-Agent": UA, "Accept": "*/*", "Referer": "https://theweekinchess.com/twic"})
    for attempt in range(6):
        try:
            body = urllib.request.urlopen(req, timeout=60).read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise
        except OSError:  # timeouts and resets: back off and retry
            if attempt == 5:
                raise
            time.sleep(10 * (attempt + 1))
    if body[:2] != b"PK":
        return None
    with open(path + ".part", "wb") as f:
        f.write(body)
    os.replace(path + ".part", path)
    time.sleep(1.0)  # be polite to a one-person site
    return path


def parse_date(s):
    m = re.match(r"(\d{4})\.(\d{2})\.(\d{2})", s or "")
    if not m or "?" in s:
        return None
    y, mo, d = (int(x) for x in m.groups())
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return "{:04d}-{:02d}-{:02d}".format(y, mo, d)


def games(text):
    """Yield (headers, movetext) pairs from a PGN string."""
    headers, moves = {}, []
    for line in text.splitlines():
        if line.startswith("["):
            if moves:
                yield headers, " ".join(moves)
                headers, moves = {}, []
            m = TAG.match(line)
            if m:
                headers[m.group(1)] = m.group(2)
        elif line.strip():
            moves.append(line)
    if moves:
        yield headers, " ".join(moves)


def parse_issue(n, path):
    z = zipfile.ZipFile(path)
    rows = []
    for name in z.namelist():
        if not name.lower().endswith(".pgn"):
            continue
        text = z.read(name).decode("latin-1")
        for h, mt in games(text):
            if "FEN" in h or h.get("SetUp") == "1" or "Variant" in h:
                continue
            plies = san_plies(mt)
            try:
                we, be = int(h.get("WhiteElo", "")), int(h.get("BlackElo", ""))
            except ValueError:
                we = be = 0
            date = parse_date(h.get("Date")) or parse_date(h.get("EventDate"))
            rows.append({
                "issue": n, "date": date, "event": h.get("Event", ""), "site": h.get("Site", ""),
                "white": h.get("White", ""), "black": h.get("Black", ""),
                "wfide": h.get("WhiteFideId", ""), "bfide": h.get("BlackFideId", ""),
                "welo": we, "belo": be, "result": h.get("Result", ""),
                "round": h.get("Round", ""), "etype": h.get("EventType", ""),
                "kind": twic_kind(h.get("Event"), h.get("Site"), h.get("EventType"), h.get("Round")),
                "nply": len(plies), "moves": " ".join(plies),
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", type=int, default=920)
    ap.add_argument("--last", type=int, default=0, help="0 = until two missing issues in a row")
    args = ap.parse_args()
    os.makedirs(RAW, exist_ok=True)

    rows, missing, n = [], 0, args.first
    while True:
        if args.last and n > args.last:
            break
        path = download(n)
        if path is None:
            missing += 1
            print("issue {} missing".format(n), flush=True)
            if missing >= 3 and not args.last:
                break
        else:
            missing = 0
            got = parse_issue(n, path)
            rows.extend(got)
            if n % 25 == 0:
                print("issue {}: {:,} games, total {:,}".format(n, len(got), len(rows)), flush=True)
        n += 1

    df = pd.DataFrame(rows)
    # Undated games inherit the median date of their issue.
    issue_date = df.dropna(subset=["date"]).groupby("issue")["date"].agg(
        lambda s: s.sort_values().iloc[len(s) // 2])
    df["date"] = df["date"].fillna(df["issue"].map(issue_date))
    # The same game can appear in two issues (late reports, corrections).
    before = len(df)
    df = df.drop_duplicates(subset=["date", "white", "black", "moves", "event"])
    print("dropped {:,} duplicate games".format(before - len(df)))
    out = os.path.join(DATA, "twic.parquet")
    df.to_parquet(out, index=False)
    print("wrote {:,} games from issues {}..{} -> {}".format(len(df), args.first, n - 1, out))


if __name__ == "__main__":
    sys.exit(main())
