"""Opening diversity per (group, period, depth).

For every cell we count how often each d-ply move sequence occurs (d = 1..20)
and report:

  H_n      plug-in Shannon entropy (bits) on a random subsample of exactly
           N_REF games, averaged over REPS draws. Entropy estimates depend on
           sample size, so every cell is measured at the same N.
  H_cs     Chao-Shen coverage-adjusted Shannon entropy on the whole cell.
  H2       collision (Renyi-2) entropy, -log2 of the chance that two
           different games drawn from the cell share their first d plies.
           The pair-coincidence estimator is unbiased for that chance at any
           N, and it does not saturate at deep plies where nearly every
           game is unique, so it is the main deep-ply measure.
  eff2     2**H2: the effective number of equally common lines.

Groups:
  lichess  speed (bullet / blitz / rapid) x rating band on the mean rating.
  twic     over-the-board classical games by the lower of the two FIDE
           ratings: 2600+ (elite), 2400-2599, 2200-2399, 2000-2199.
           Online and rapid/blitz events are kept as separate groups.

Output: out/cells.parquet
Usage:  python entropy.py [--nref 200] [--reps 5]
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd

from common import DATA, LICHESS_BANDS, OUT, PLIES

LN2 = np.log(2.0)
TWIC_BANDS = [(2600, 4000, "2600+"), (2400, 2600, "2400-2599"),
              (2200, 2400, "2200-2399"), (2000, 2200, "2000-2199")]


def prefix_codes(moves):
    """(n_games, PLIES) int64 array: column d-1 identifies the d-ply prefix."""
    toks = moves.str.split(" ", expand=True).reindex(columns=range(PLIES))
    codes = np.empty((len(moves), PLIES), dtype=np.int64)
    prev = np.zeros(len(moves), dtype=np.int64)
    for d in range(PLIES):
        t = pd.factorize(toks[d], use_na_sentinel=False)[0].astype(np.int64)
        prev = pd.factorize(prev * (t.max() + 1) + t)[0].astype(np.int64)
        codes[:, d] = prev
    return codes


def cell_stats(counts):
    """Estimators from the vector of sequence counts of one cell."""
    n = counts.astype(float)
    N = n.sum()
    p = n / N
    h_plug = -(p * np.log2(p)).sum()
    f1 = (counts == 1).sum()
    if f1 == N:
        f1 = N - 1
    C = 1 - f1 / N
    pa = C * p
    h_cs = -(pa * np.log2(pa) / (1 - (1 - pa) ** N)).sum()
    s2 = (n * (n - 1)).sum() / (N * (N - 1))
    h2 = -np.log2(s2) if s2 > 0 else np.nan
    return h_plug, h_cs, s2, h2, len(counts)


def cells_for(frame, keys, nref, reps, seed):
    """frame: games with key columns + 'moves'. Returns one row per cell x depth."""
    frame = frame.reset_index(drop=True)
    codes = prefix_codes(frame["moves"])
    cell = frame.groupby(keys, sort=False).ngroup().to_numpy()
    cell_keys = frame[keys].drop_duplicates().reset_index(drop=True)
    cell_keys["cid"] = frame.groupby(keys, sort=False).ngroup().drop_duplicates().to_numpy()
    rng = np.random.default_rng(seed)
    # one random rank per game per rep; a game is in rep r's subsample if its rank < nref
    ranks = []
    for r in range(reps):
        u = rng.random(len(frame))
        ranks.append(pd.Series(u).groupby(cell).rank(method="first").to_numpy() - 1)
    out = []
    for cid, idx in pd.Series(np.arange(len(frame))).groupby(cell):
        idx = idx.to_numpy()
        N = len(idx)
        sub = [idx[ranks[r][idx] < nref] for r in range(reps)] if N >= nref else None
        for d in range(PLIES):
            c = codes[idx, d]
            counts = np.bincount(pd.factorize(c)[0])
            h_plug, h_cs, s2, h2, K = cell_stats(counts)
            if sub is not None:
                hn = np.mean([cell_stats(np.bincount(pd.factorize(codes[s, d])[0]))[0] for s in sub])
            else:
                hn = np.nan
            out.append((cid, d + 1, N, K, h_plug, h_cs, hn, s2, h2))
    res = pd.DataFrame(out, columns=["cid", "depth", "N", "K", "H_plug", "H_cs", "H_n", "S2", "H2"])
    res["eff2"] = 2 ** res["H2"]
    return cell_keys.merge(res, on="cid").drop(columns="cid")


def band_of(x, bands):
    out = pd.Series(pd.NA, index=x.index, dtype="object")
    for lo, hi, name in bands:
        out[(x >= lo) & (x < hi)] = name
    return out


def quarter(month):
    y, m = month.str[:4], month.str[5:7].astype(int)
    return y + "Q" + ((m - 1) // 3 + 1).astype(str)


def lichess_games(path, cap):
    df = pd.read_parquet(path, columns=["month", "speed", "welo", "belo", "term", "nply", "moves"])
    df = df[(df.nply == PLIES) & (df.term != "Abandoned")
            & df.speed.isin(["bullet", "blitz", "rapid"])]
    df = df.assign(band=band_of((df.welo + df.belo) / 2, LICHESS_BANDS)).dropna(subset=["band"])
    # Cap each month x speed x band at `cap` games: the collision estimator is
    # unbiased at any N and H_n uses 200, so the extra games only cost memory.
    df = df.sample(frac=1.0, random_state=0).groupby(["speed", "band"]).head(cap)
    return df[["month", "speed", "band", "moves"]]


def lichess_cells(nref, reps, cap=5000):
    """Processed one calendar year at a time to keep memory bounded."""
    files = sorted(glob.glob(os.path.join(DATA, "lichess", "*.parquet")))
    years = sorted({os.path.basename(f)[:4] for f in files})
    cache = os.path.join(OUT, "cache")
    os.makedirs(cache, exist_ok=True)
    res = []
    for y in years:
        path = os.path.join(cache, "lichess_{}_n{}.parquet".format(y, nref))
        if os.path.exists(path):  # resumable: one finished year per file
            res.append(pd.read_parquet(path))
            continue
        games = pd.concat([lichess_games(f, cap) for f in files if os.path.basename(f)[:4] == y],
                          ignore_index=True)
        games["quarter"] = quarter(games["month"])
        games["year"] = games["month"].str[:4]
        yr = []
        for ptype in ["month", "quarter", "year"]:
            g = games.rename(columns={ptype: "period"})[["period", "speed", "band", "moves"]]
            r = cells_for(g, ["period", "speed", "band"], nref, reps, seed=1)
            r["ptype"] = ptype
            yr.append(r)
        yr = pd.concat(yr, ignore_index=True)
        yr.to_parquet(path, index=False)
        res.append(yr)
        print("lichess {}: {:,} games".format(y, len(games)), flush=True)
    out = pd.concat(res, ignore_index=True)
    out["source"] = "lichess"
    return out


def twic_games():
    df = pd.read_parquet(os.path.join(DATA, "twic.parquet"))
    df = df[(df.nply == PLIES) & df.date.notna()]
    lo = df[["welo", "belo"]].min(axis=1)
    df = df.assign(band=band_of(lo, TWIC_BANDS)).dropna(subset=["band"])
    df["month"] = df["date"].str[:7]
    df = df[(df.month >= "2012-07") & (df.month <= "2026-12")]
    return df


def twic_cells(nref, reps):
    df = twic_games()
    df["quarter"] = quarter(df["month"])
    df["year"] = df["month"].str[:4]
    res = []
    for ptype in ["quarter", "year"]:
        g = df.rename(columns={ptype: "period", "kind": "speed"})[["period", "speed", "band", "moves"]]
        r = cells_for(g, ["period", "speed", "band"], nref, reps, seed=2)
        r["ptype"] = ptype
        res.append(r)
    out = pd.concat(res, ignore_index=True)
    out["source"] = "twic"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nref", type=int, default=200)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--only", choices=["twic", "lichess"], default=None)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    parts = []
    if args.only != "lichess":
        parts.append(twic_cells(args.nref, args.reps))
    if args.only != "twic":
        parts.append(lichess_cells(args.nref, args.reps))
    out = pd.concat(parts, ignore_index=True)
    name = "cells.parquet" if args.only is None else "cells_{}.parquet".format(args.only)
    out.to_parquet(os.path.join(OUT, name), index=False)
    print("wrote {:,} rows".format(len(out)))


if __name__ == "__main__":
    main()
