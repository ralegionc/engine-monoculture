"""Breakpoint tests on the diversity series.

For each group series y_t (one depth, one metric, quarterly):

  segmented   y = a + b t + c (t - T0)+ + d 1[t >= T0] at each known engine
              date T0, Newey-West (HAC, 4 lags) standard errors. c is the
              change in trend, d the jump.
  placebo     the same fit at every quarter 2015-2024: a real break at an
              engine date should make the jump t statistic peak there.
  supF        unknown single break (trend and level), searched over the middle
              70% of the sample, p value by AR(1) residual bootstrap under a
              straight line.

Gap series: amateur minus elite (Lichess band minus TWIC 2600+ classical),
the quantity the hypothesis says should keep widening after the engines.

Output: out/breaks.csv, out/placebo.csv, out/supf.csv
"""
import argparse
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm

from common import EVENTS, OUT

DEPTHS = [2, 4, 6, 8, 10, 12, 16, 20]
ELITE = ("twic", "classical", "2600+")


def tnum(period):
    """'2019Q3' -> 2019.625 (quarter midpoint); '2019' -> 2019.5; '2019-03' -> 2019.208."""
    p = str(period)
    if "Q" in p:
        y, q = p.split("Q")
        return int(y) + (int(q) - 0.5) / 4
    if "-" in p:
        y, m = p.split("-")
        return int(y) + (int(m) - 0.5) / 12
    return int(p) + 0.5


def ev_t(month):
    y, m = month.split("-")
    return int(y) + (int(m) - 1) / 12


def series(cells, source, speed, band, depth, metric="H2", ptype="quarter", min_n=150,
           start=2013.0, end=2026.75):
    c = cells[(cells.source == source) & (cells.speed == speed) & (cells.band == band)
              & (cells.depth == depth) & (cells.ptype == ptype) & (cells.N >= min_n)]
    s = pd.Series(c[metric].to_numpy(), index=[tnum(p) for p in c.period]).sort_index()
    return s[(s.index >= start) & (s.index < end)].dropna()


def design(t, T0):
    post = (t >= T0).astype(float)
    return np.column_stack([np.ones_like(t), t - T0, np.clip(t - T0, 0, None), post])


def segfit(s, T0, lags=4):
    t, y = s.index.to_numpy(float), s.to_numpy(float)
    if (t < T0).sum() < 6 or (t >= T0).sum() < 6:
        return None
    r = sm.OLS(y, design(t, T0)).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    b, se = r.params, r.bse
    return {"n": len(y), "pre_slope": b[1], "post_slope": b[1] + b[2], "dslope": b[2],
            "dslope_se": se[2], "dslope_t": b[2] / se[2], "dslope_p": r.pvalues[2],
            "jump": b[3], "jump_se": se[3], "jump_p": r.pvalues[3]}


def sup_f(s, trim=0.15, boot=499, seed=0):
    t, y = s.index.to_numpy(float), s.to_numpy(float)
    n = len(y)
    X0 = np.column_stack([np.ones(n), t - t.mean()])

    def stat(yv):
        rss0 = np.sum((yv - X0 @ np.linalg.lstsq(X0, yv, rcond=None)[0]) ** 2)
        best, arg = -np.inf, None
        for k in range(int(n * trim), int(n * (1 - trim))):
            X = design(t, t[k])
            rss1 = np.sum((yv - X @ np.linalg.lstsq(X, yv, rcond=None)[0]) ** 2)
            f = ((rss0 - rss1) / 2) / (rss1 / (n - 4))
            if f > best:
                best, arg = f, t[k]
        return best, arg

    F, at = stat(y)
    fit0 = X0 @ np.linalg.lstsq(X0, y, rcond=None)[0]
    e = y - fit0
    rho = np.corrcoef(e[:-1], e[1:])[0, 1]
    u = e[1:] - rho * e[:-1]
    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(boot):
        uu = rng.choice(u, n)
        eb = np.empty(n)
        eb[0] = rng.choice(e)
        for i in range(1, n):
            eb[i] = rho * eb[i - 1] + uu[i]
        exceed += stat(fit0 + eb)[0] >= F
    return {"n": n, "supF": F, "break_at": at, "p_boot": (exceed + 1) / (boot + 1), "ar1": rho}


def groups(cells):
    """Every (source, speed, band) series worth testing."""
    g = cells[cells.ptype == "quarter"][["source", "speed", "band"]].drop_duplicates()
    keep = g[(g.source == "lichess") | (g.speed == "classical")]
    return [tuple(x) for x in keep.itertuples(index=False)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", default="H2")
    ap.add_argument("--boot", type=int, default=299)
    args = ap.parse_args()
    cells = pd.read_parquet(os.path.join(OUT, "cells.parquet"))

    rows, plac, sup = [], [], []
    amateurs = [g for g in groups(cells) if g[0] == "lichess"]
    for d in DEPTHS:
        elite = series(cells, *ELITE, d, args.metric)
        targets = [(g, series(cells, *g, d, args.metric)) for g in groups(cells)]
        for g in amateurs:
            a = series(cells, *g, d, args.metric)
            gap = (a - elite).dropna()
            targets.append(((g[0], g[1], g[2] + " minus elite"), gap))
        for (src, spd, band), s in targets:
            if len(s) < 16:
                continue
            for name, month in EVENTS.items():
                f = segfit(s, ev_t(month))
                if f:
                    rows.append({"source": src, "speed": spd, "band": band, "depth": d,
                                 "event": name, **f})
            is_main = (src, spd, band) == ELITE or (spd == "blitz" and "minus" in band) \
                or (src == "lichess" and spd == "blitz")
            if not is_main:
                continue
            ts = [x for x in s.index if 2015.0 <= x <= 2024.0]
            for T0 in ts:
                f = segfit(s, T0)
                if f:
                    plac.append({"source": src, "speed": spd, "band": band, "depth": d,
                                 "T0": T0, "dslope_t": f["dslope_t"], "jump": f["jump"],
                                 "jump_t": f["jump"] / f["jump_se"],
                                 "dslope": f["dslope"]})
            if d in (4, 8, 12) and ((src, spd, band) == ELITE or spd == "blitz"):
                sup.append({"source": src, "speed": spd, "band": band, "depth": d,
                            **sup_f(s, boot=args.boot)})
        print("depth {} done".format(d), flush=True)

    suffix = "" if args.metric == "H2" else "_" + args.metric
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "breaks{}.csv".format(suffix)), index=False)
    pd.DataFrame(plac).to_csv(os.path.join(OUT, "placebo{}.csv".format(suffix)), index=False)
    pd.DataFrame(sup).to_csv(os.path.join(OUT, "supf{}.csv".format(suffix)), index=False)
    print("wrote breaks / placebo / supf")


if __name__ == "__main__":
    main()
