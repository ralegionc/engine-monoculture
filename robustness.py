"""Era comparisons with cluster bootstrap, and a fixed-event check.

Era table: for every group and depth, collision entropy H2 pooled over
PRE (2014-2017) and POST (2022-2025). The 2018-2021 window, which holds
AlphaZero, Leela, NNUE and the pandemic stop in over-the-board chess, is left
out so neither era straddles it. Confidence intervals come from resampling
whole clusters (TWIC: events, since an event's games share fashions; Lichess:
months), 300 draws.

Fixed events: TWIC coverage changes over time. Restricting to tournaments that
recur in both eras (names with years, ordinals and roman numerals removed)
holds the event mix roughly constant.

Output: out/era.csv, out/fixed_events.csv
"""
import glob
import os
import re

import numpy as np
import pandas as pd
from scipy import sparse

from common import DATA, OUT
from entropy import lichess_games, prefix_codes, twic_games

PRE, POST = ("2014", "2017"), ("2022", "2025")
DEPTHS = [2, 4, 6, 8, 10, 12, 14, 16, 20]
B = 300


def h2_boot(codes, cluster, rng, boot=B):
    """H2 point estimate and bootstrap draws, resampling clusters."""
    cl = pd.factorize(cluster)[0]
    sq = pd.factorize(codes)[0]
    M = sparse.csr_matrix((np.ones(len(sq)), (cl, sq)))  # clusters x sequences
    sizes = np.asarray(M.sum(axis=1)).ravel()

    def h2(w):
        # A cluster drawn twice must not pair each game with its own copy:
        # drop those w(w-1) same-game pairs from matches and from all pairs.
        n = M.T @ w
        dup = M.T @ (w * (w - 1))
        N = sizes @ w
        match = (n * n - n - dup).sum()
        pairs = N * N - N - (sizes * w * (w - 1)).sum()
        return -np.log2(match / pairs)

    k = M.shape[0]
    point = h2(np.ones(k))
    draws = np.array([h2(np.bincount(rng.integers(0, k, k), minlength=k).astype(float))
                      for _ in range(boot)])
    return point, draws


def era_rows(df, group, cluster_col, rng):
    rows = []
    era = np.where(df.year.between(*PRE), "pre", np.where(df.year.between(*POST), "post", ""))
    df = df.assign(era=era)
    df = df[df.era != ""].reset_index(drop=True)
    if df.era.nunique() < 2:
        return rows
    codes = prefix_codes(df["moves"])
    for d in DEPTHS:
        res = {}
        for e in ["pre", "post"]:
            m = (df.era == e).to_numpy()
            res[e] = h2_boot(codes[m, d - 1], df.loc[m, cluster_col].to_numpy(), rng)
        diff = res["post"][1] - res["pre"][1]
        rows.append({**group, "depth": d,
                     "n_pre": int((df.era == "pre").sum()), "n_post": int((df.era == "post").sum()),
                     "pre": res["pre"][0], "post": res["post"][0],
                     "diff": res["post"][0] - res["pre"][0],
                     "lo": np.percentile(diff, 2.5), "hi": np.percentile(diff, 97.5),
                     "draws": diff})
    return rows


_EVNORM = [re.compile(p, re.I) for p in [r"\b(19|20)\d\d\b", r"\b\d+(st|nd|rd|th)\b", r"\b[ivxlc]+\b",
                                          r"\d+", r"[^a-z ]"]]


def event_key(name):
    s = name.lower()
    for p in _EVNORM:
        s = p.sub(" ", s)
    return " ".join(s.split())


def main():
    rng = np.random.default_rng(0)
    rows = []

    tw = twic_games()
    tw["year"] = tw["month"].str[:4]
    tw["cluster"] = tw["event"] + "|" + tw["year"]
    for band in ["2600+", "2400-2599", "2200-2399", "2000-2199"]:
        sub = tw[(tw.kind == "classical") & (tw.band == band)]
        rows += era_rows(sub, {"source": "twic", "speed": "classical", "band": band}, "cluster", rng)
        print("twic", band, flush=True)

    files = sorted(f for f in glob.glob(os.path.join(DATA, "lichess", "*.parquet"))
                   if PRE[0] <= os.path.basename(f)[:4] <= POST[1])
    li = pd.concat([lichess_games(f, 5000) for f in files], ignore_index=True)
    li["year"] = li["month"].str[:4]
    for (spd, band), sub in li.groupby(["speed", "band"]):
        rows += era_rows(sub, {"source": "lichess", "speed": spd, "band": band}, "month", rng)
        print("lichess", spd, band, flush=True)

    era = pd.DataFrame(rows)
    # gap = amateur change minus elite change, independent bootstraps
    elite = era[(era.source == "twic") & (era.band == "2600+")].set_index("depth")
    gaps = []
    for _, r in era[era.source == "lichess"].iterrows():
        e = elite.loc[r.depth]
        g = r.draws - e.draws
        gaps.append({"source": "gap", "speed": r.speed, "band": r.band + " minus elite", "depth": r.depth,
                     "diff": r["diff"] - e["diff"], "lo": np.percentile(g, 2.5), "hi": np.percentile(g, 97.5)})
    era = pd.concat([era, pd.DataFrame(gaps)], ignore_index=True).drop(columns="draws")
    era.to_csv(os.path.join(OUT, "era.csv"), index=False)

    # fixed events
    tw["ekey"] = tw["event"].map(event_key)
    cl = tw[tw.kind == "classical"]
    pre_keys = set(cl[cl.year.between(*PRE)].ekey)
    post_keys = set(cl[cl.year.between(*POST)].ekey)
    keep = pre_keys & post_keys
    fixed = []
    for band in ["2600+", "2200-2399"]:
        sub = cl[(cl.band == band) & cl.ekey.isin(keep)]
        for r in era_rows(sub, {"source": "twic_fixed", "speed": "classical", "band": band}, "cluster", rng):
            r.pop("draws")
            r["events"] = len(keep)
            fixed.append(r)
    pd.DataFrame(fixed).to_csv(os.path.join(OUT, "fixed_events.csv"), index=False)
    print("wrote era.csv, fixed_events.csv ({} recurring event names)".format(len(keep)))


if __name__ == "__main__":
    main()
