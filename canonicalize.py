"""Rewrite Lichess moves in canonical SAN.

The 2013 and early-2014 Lichess dumps over-disambiguate some moves ('Ng8e7'
for 'N8e7', 'Nb4c6' for 'N4c6'). It is rare until September 2013, then hits
up to 17% of games (115,517 rewritten in the January 2014 sample) until it
stops in July 2014. validate.py finds none after that, and none in TWIC. An extra letter
would split one line into two, so games in the 2013-2014 files that contain a
disambiguated piece move are replayed with python-chess.

Each month file gets a 'canon' column once done; reruns skip it.
Usage:  python canonicalize.py [--jobs 3]
"""
import argparse
import glob
import os
import re
from concurrent.futures import ProcessPoolExecutor

import chess
import pandas as pd

from common import DATA

DISAMB = re.compile(r"(?:^| )[NBRQK][a-h1-8]x?[a-h][1-8]|(?:^| )[NBRQK][a-h][1-8]x?[a-h][1-8]")


def canon(moves):
    b = chess.Board()
    out = []
    for tok in moves.split():
        try:
            m = b.parse_san(tok)
        except ValueError:
            return moves
        out.append(b.san(m).rstrip("+#"))
        b.push(m)
    return " ".join(out)


def do_file(path):
    df = pd.read_parquet(path)
    if "canon" in df.columns:
        return path, -1
    mask = df["moves"].str.contains(DISAMB)
    new = df.loc[mask, "moves"].map(canon)
    changed = int((new != df.loc[mask, "moves"]).sum())
    df.loc[mask, "moves"] = new
    df["canon"] = True
    df.to_parquet(path + ".part", index=False)
    os.replace(path + ".part", path)
    return path, changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=3)
    args = ap.parse_args()
    files = sorted(f for f in glob.glob(os.path.join(DATA, "lichess", "*.parquet"))
                   if os.path.basename(f) < "2015")
    with ProcessPoolExecutor(args.jobs) as ex:
        for path, n in ex.map(do_file, files):
            if n >= 0:
                print("{}  {:,} games rewritten".format(os.path.basename(path), n), flush=True)


if __name__ == "__main__":
    main()
