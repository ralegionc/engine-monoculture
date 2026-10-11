"""Print every number the README quotes, from the files in out/.

Usage:  python report.py > out/summary.md
"""
import glob
import os

import pandas as pd

from common import DATA, OUT
from entropy import twic_games


def era_row(era, source, speed, band, depth):
    r = era[(era.source == source) & (era.speed == speed) & (era.band == band) & (era.depth == depth)].iloc[0]
    return r


def fmt(r, eff=False):
    s = "{:+.2f} bits [{:+.2f}, {:+.2f}]".format(r["diff"], r["lo"], r["hi"])
    if eff and pd.notna(r.get("pre")):
        s += "; {:.2f} -> {:.2f} bits, {:.1f} -> {:.1f} effective lines".format(
            r["pre"], r["post"], 2 ** r["pre"], 2 ** r["post"])
    return s


def main():
    era = pd.read_csv(os.path.join(OUT, "era.csv"))
    fixed = pd.read_csv(os.path.join(OUT, "fixed_events.csv"))
    breaks = pd.read_csv(os.path.join(OUT, "breaks.csv"))
    supf = pd.read_csv(os.path.join(OUT, "supf.csv"))
    plac = pd.read_csv(os.path.join(OUT, "placebo.csv"))
    pyr = pd.read_csv(os.path.join(OUT, "players_year.csv"))
    pan = pd.read_csv(os.path.join(OUT, "players_panel.csv"))
    cells = pd.read_parquet(os.path.join(OUT, "cells.parquet"))

    print("# Summary numbers\n")
    print("## Data")
    n_li = sum(pd.read_parquet(f, columns=["month"]).shape[0]
               for f in glob.glob(os.path.join(DATA, "lichess", "*.parquet")))
    tw = twic_games()
    print("- Lichess games sampled: {:,} over {} months".format(
        n_li, len(glob.glob(os.path.join(DATA, "lichess", "*.parquet")))))
    print("- TWIC games with 20 plies and both ratings >= 2000: {:,}".format(len(tw)))
    print("- of which OTB classical 2600+: {:,}".format(((tw.kind == "classical") & (tw.band == "2600+")).sum()))
    print("- online / fast games excluded from the OTB series: {:,} / {:,}".format(
        (tw.kind == "online").sum(), (tw.kind == "fast").sum()))

    print("\n## Era change, collision entropy, 2022-25 vs 2014-17 (95% cluster bootstrap)")
    for src, spd, band in [("twic", "classical", "2600+"), ("twic", "classical", "2400-2599"),
                           ("twic", "classical", "2200-2399"), ("twic", "classical", "2000-2199"),
                           ("lichess", "blitz", "2400+"), ("lichess", "blitz", "2100-2399"),
                           ("lichess", "blitz", "1800-2099"), ("lichess", "blitz", "1500-1799"),
                           ("lichess", "blitz", "1200-1499"), ("lichess", "blitz", "<1200"),
                           ("lichess", "rapid", "1800-2099"), ("lichess", "bullet", "1800-2099")]:
        for d in [4, 8, 12, 16]:
            print("- {} {} {} @{}: {}".format(src, spd, band, d, fmt(era_row(era, src, spd, band, d), eff=(d == 4))))

    print("\n## Gap (Lichess blitz band change minus elite change)")
    for band in ["2400+", "2100-2399", "1800-2099", "1500-1799", "1200-1499", "<1200"]:
        for d in [4, 8, 12]:
            print("- {} @{}: {}".format(band, d, fmt(era_row(era, "gap", "blitz", band + " minus elite", d))))

    print("\n## Fixed recurring events ({} event names)".format(int(fixed.events.iloc[0])))
    for _, r in fixed[fixed.depth.isin([2, 4, 8, 12, 16])].iterrows():
        print("- {} @{}: {} (n {:,} -> {:,})".format(r.band, r.depth, fmt(r), r.n_pre, r.n_post))

    print("\n## Breakpoints, elite 2600+ (quarterly H2, HAC SE)")
    b = breaks[(breaks.source == "twic") & (breaks.band == "2600+") & breaks.depth.isin([4, 8, 12])]
    for _, r in b.iterrows():
        print("- @{} {}: jump {:+.2f} (p {:.3f}), trend {:+.3f} -> {:+.3f} bits/yr (p {:.3f})".format(
            r.depth, r.event, r.jump, r.jump_p, r.pre_slope, r.post_slope, r.dslope_p))
    for _, r in supf.iterrows():
        if r.band in ("2600+", "1800-2099 minus elite", "1200-1499 minus elite"):
            print("- supF {} @{}: break at {:.2f}, F {:.1f}, bootstrap p {:.3f}".format(
                r.band, r.depth, r.break_at, r.supF, r.p_boot))
    for band in ["2600+", "1800-2099 minus elite"]:
        s = plac[(plac.band == band) & (plac.depth == 4)]
        i = s.jump_t.abs().idxmax()
        print("- placebo scan {} @4: largest |jump t| at {:.2f} (t {:.1f})".format(band, s.loc[i, "T0"], s.loc[i, "jump_t"]))

    print("\n## Shannon check (plug-in at N=200, yearly cells, mean 2022-25 minus mean 2014-17)")
    y = cells[(cells.ptype == "year") & cells.depth.isin([2, 4, 6])]
    y = y.assign(yr=y.period.astype(int))
    for src, spd, band in [("twic", "classical", "2600+"), ("twic", "classical", "2200-2399"),
                           ("lichess", "blitz", "1800-2099"), ("lichess", "blitz", "1200-1499")]:
        g = y[(y.source == src) & (y.speed == spd) & (y.band == band)]
        for d in [2, 4, 6]:
            gd = g[g.depth == d]
            pre = gd[gd.yr.between(2014, 2017)].H_n.mean()
            post = gd[gd.yr.between(2022, 2025)].H_n.mean()
            print("- {} {} @{}: {:.2f} -> {:.2f} ({:+.2f})".format(src, band, d, pre, post, post - pre))

    print("\n## Players (elite 2600+, White repertoires)")
    for d in [4, 8]:
        s = pyr[(pyr.depth == d)].set_index("year")
        pre = s.loc[2014:2017, ["within", "between"]].mean()
        post = s.loc[2022:2025, ["within", "between"]].mean()
        print("- @{} yearly mean, same player: {:.1%} -> {:.1%}; different players: {:.1%} -> {:.1%}".format(
            d, pre["within"], post["within"], pre["between"], post["between"]))
    p = pan.dropna(subset=["diff"])
    for _, r in p[p.depth.isin([2, 4, 6, 8, 12])].iterrows():
        print("- panel ({} players) @{}: self-repeat {:.1%} -> {:.1%} ({:+.1f} pts [{:+.1f}, {:+.1f}]), {:.0%} rose".format(
            int(r.players), int(r.depth), r.pre, r.post, r["diff"] * 100, r.lo * 100, r.hi * 100, r.share_up))
    q = pan[pan.era.notna()].pivot_table(index="depth", columns="era", values="between")
    for d in [4, 8]:
        print("- panel between-player match @{}: {:.1%} -> {:.1%}".format(d, q.loc[d, "pre"], q.loc[d, "post"]))

    print("\n## Elite 4-ply line shares (% of OTB classical 2600+ games)")
    e = tw[(tw.kind == "classical") & (tw.band == "2600+")].copy()
    e["yr"] = e.month.str[:4].astype(int)
    e["p4"] = e.moves.str.split().str[:4].str.join(" ")
    e["era"] = pd.cut(e.yr, [2013, 2017, 2021, 2025], labels=["2014-17", "2018-21", "2022-25"])
    t = pd.crosstab(e.p4, e.era, normalize="columns") * 100
    print(t.loc[t.max(axis=1).sort_values(ascending=False).index[:8]].round(1).to_markdown())


if __name__ == "__main__":
    main()
