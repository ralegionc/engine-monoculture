"""Check that both sources spell the same move the same way.

Opening sequences are compared as strings, so an over-disambiguated move
("Nbd2" where "Nd2" is enough) would split one line into two. We replay a
random sample of games from each source with python-chess and count plies
whose stored token differs from the canonical SAN (check marks stripped).

Output: out/validate.txt
"""
import glob
import os

import chess
import pandas as pd

from common import DATA, OUT


def check(moves_series, n=20000, seed=0):
    sample = moves_series.sample(min(n, len(moves_series)), random_state=seed)
    plies = bad = illegal = 0
    examples = []
    for mv in sample:
        b = chess.Board()
        for tok in mv.split():
            plies += 1
            try:
                m = b.parse_san(tok)
            except ValueError:
                illegal += 1
                if len(examples) < 5:
                    examples.append(("illegal", mv, tok))
                break
            canon = b.san(m).rstrip("+#")
            if canon != tok:
                bad += 1
                if len(examples) < 5:
                    examples.append(("non-canonical", tok, canon))
            b.push(m)
    return plies, bad, illegal, examples


def main():
    lines = []
    tw = pd.read_parquet(os.path.join(DATA, "twic.parquet"), columns=["moves"])
    files = sorted(glob.glob(os.path.join(DATA, "lichess", "*.parquet")))
    li = pd.concat([pd.read_parquet(f, columns=["moves"]) for f in files[::12]])
    for name, s in [("twic", tw.moves), ("lichess", li.moves)]:
        plies, bad, illegal, ex = check(s[s.str.len() > 0])
        lines.append("{}: {:,} plies, {:,} non-canonical ({:.4%}), {:,} unparseable games".format(
            name, plies, bad, bad / plies, illegal))
        lines += ["   {}".format(e) for e in ex]
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(OUT, "validate.txt"), "w") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
