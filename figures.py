"""Figures for the README (PNG, light background)."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from breaks import ev_t, series  # noqa: E402
from common import EVENTS, FIG, OUT  # noqa: E402
from entropy import twic_games  # noqa: E402

SURFACE = "#fcfcfb"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0"
SLOT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
DIVERGE = LinearSegmentedColormap.from_list("div", ["#a3302f", "#e34948", "#f0efec", "#2a78d6", "#104281"])

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "lines.linewidth": 2,
})

GROUPS = [  # (source, speed, band, label, color)
    ("twic", "classical", "2600+", "OTB elite 2600+", SLOT[0]),
    ("twic", "classical", "2200-2399", "OTB 2200-2399", SLOT[6]),
    ("lichess", "blitz", "2400+", "Lichess blitz 2400+", SLOT[2]),
    ("lichess", "blitz", "1800-2099", "Lichess blitz 1800-2099", SLOT[1]),
    ("lichess", "blitz", "1200-1499", "Lichess blitz 1200-1499", SLOT[4]),
]


def shade(ax):
    ax.axvspan(2018, 2022, color="#efeee9", zorder=0, lw=0)
    for name, m in EVENTS.items():
        ax.axvline(ev_t(m), color=MUTED, lw=0.8, ls=(0, (3, 3)), zorder=1)


def label_ends(ax, items):
    """Direct labels at the right end, nudged apart vertically."""
    items = sorted(items, key=lambda t: t[1])
    lo, hi = ax.get_ylim()
    gap = (hi - lo) * 0.055
    placed = []
    for text, y, color in items:
        if placed and y - placed[-1] < gap:
            y = placed[-1] + gap
        placed.append(y)
        ax.annotate(text, xy=(1.01, (y - lo) / (hi - lo)), xycoords="axes fraction",
                    color=INK2, fontsize=8.5, va="center",
                    bbox=dict(boxstyle="square,pad=0.1", fc=SURFACE, ec="none"))
        ax.plot([1.0], [(y - lo) / (hi - lo)], marker="s", ms=6, color=color,
                transform=ax.transAxes, clip_on=False)


def fig_series(cells):
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6))
    for ax, d in zip(axes, [4, 12]):
        shade(ax)
        ends = []
        for src, spd, band, lab, col in GROUPS:
            s = series(cells, src, spd, band, d, "H2", ptype="year", min_n=300, end=2027)
            s = s[s.index >= 2014]
            ax.plot(s.index, s.values, color=col, marker="o", ms=4)
            ends.append((lab, s.values[-1], col))
        ax.set_title("{} plies".format(d) + (" (first two moves each)" if d == 4 else " (six moves each)"),
                     loc="left")
        ax.set_ylabel("collision entropy, bits")
        ax.set_xlim(2013.6, 2026.9)
        label_ends(ax, ends)
    axes[0].text(2018.1, axes[0].get_ylim()[1], " 2018-2021: AlphaZero, Leela,\n NNUE, pandemic",
                 va="top", fontsize=8, color=INK2)
    fig.suptitle("Over-the-board players narrowed their early moves; online club players did not",
                 x=0.01, ha="left", fontsize=12.5, fontweight="bold")
    fig.text(0.01, 0.005, "Higher = more varied. One point per year (2026: Jan-Sep). Dashed: AlphaZero paper (Dec 2017), "
             "Leela wins TCEC (May 2019), Stockfish 12 NNUE (Sep 2020). Shaded: 2018-2021, which also "
             "holds the pandemic stop in over-the-board play.",
             fontsize=8, color=INK2)
    fig.subplots_adjust(left=0.05, right=0.84, wspace=0.55, top=0.85, bottom=0.12)
    fig.savefig(os.path.join(FIG, "fig1_series.png"), dpi=160)
    plt.close(fig)


def fig_heatmap(era):
    rows = [("twic", "classical", "2600+", "OTB 2600+ (elite)"), ("twic", "classical", "2400-2599", "OTB 2400-2599"),
            ("twic", "classical", "2200-2399", "OTB 2200-2399"), ("twic", "classical", "2000-2199", "OTB 2000-2199"),
            ("lichess", "blitz", "2400+", "Lichess blitz 2400+"), ("lichess", "blitz", "2100-2399", "Lichess blitz 2100-2399"),
            ("lichess", "blitz", "1800-2099", "Lichess blitz 1800-2099"), ("lichess", "blitz", "1500-1799", "Lichess blitz 1500-1799"),
            ("lichess", "blitz", "1200-1499", "Lichess blitz 1200-1499"), ("lichess", "blitz", "<1200", "Lichess blitz <1200")]
    depths = sorted(era.depth.unique())
    M = np.full((len(rows), len(depths)), np.nan)
    sig = np.zeros_like(M, dtype=bool)
    for i, (src, spd, band, _) in enumerate(rows):
        for j, d in enumerate(depths):
            r = era[(era.source == src) & (era.speed == spd) & (era.band == band) & (era.depth == d)]
            if len(r):
                M[i, j] = r["diff"].iloc[0]
                sig[i, j] = r["lo"].iloc[0] > 0 or r["hi"].iloc[0] < 0
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    lim = np.nanmax(np.abs(M))
    im = ax.imshow(M, cmap=DIVERGE, vmin=-lim, vmax=lim, aspect="auto")
    ax.grid(False)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            txt = "{:+.2f}".format(v) if sig[i, j] else "({:+.1f})".format(v)
            ax.text(j, i, txt, ha="center", va="center", fontsize=8,
                    color="white" if abs(v) > 0.6 * lim else INK)
    ax.axhline(3.5, color=SURFACE, lw=4)
    ax.set_xticks(range(len(depths)), [str(d) for d in depths])
    ax.set_yticks(range(len(rows)), [r[3] for r in rows])
    ax.set_xlabel("depth (plies)")
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("change in bits, 2022-25 vs 2014-17")
    cb.outline.set_visible(False)
    ax.set_title("Change in opening diversity by depth. Red: narrower, blue: wider", loc="left")
    fig.text(0.01, 0.01, "Collision entropy, eras pooled. Parentheses: 95% cluster-bootstrap interval "
             "includes zero.", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(FIG, "fig2_depth_heatmap.png"), dpi=160)
    plt.close(fig)


LINES = [("e4 e5 Nf3 Nc6", "1.e4 e5 2.Nf3 Nc6 (Italian, Spanish)"),
         ("d4 Nf6 c4 e6", "1.d4 Nf6 2.c4 e6 (Nimzo, QGD)"),
         ("e4 c5 Nf3 d6", "1.e4 c5 2.Nf3 d6 (Open Sicilian)"),
         ("d4 Nf6 c4 g6", "1.d4 Nf6 2.c4 g6 (King's Indian, Grunfeld)"),
         ("d4 d5 c4 c6", "1.d4 d5 2.c4 c6 (Slav)")]


def fig_lines():
    d = twic_games()
    d = d[(d.kind == "classical") & (d.band == "2600+")].copy()
    d["year"] = d.month.str[:4].astype(int)
    d = d[d.year >= 2013]
    d["p4"] = d.moves.str.split().str[:4].str.join(" ")
    share = pd.crosstab(d.year, d.p4, normalize="index") * 100
    fig, ax = plt.subplots(figsize=(10, 4.6))
    shade(ax)
    ends = []
    for (k, lab), col in zip(LINES, SLOT):
        ax.plot(share.index + 0.5, share[k], color=col, marker="o", ms=4)
        ends.append((lab, share[k].iloc[-1], col))
    ax.set_ylabel("% of elite classical games")
    ax.set_xlim(2013.2, 2026.9)
    ax.set_ylim(0, None)
    label_ends(ax, ends)
    ax.set_title("Elite players converged on 1.e4 e5 and away from the King's Indian and Slav", loc="left")
    fig.subplots_adjust(left=0.07, right=0.66, top=0.9, bottom=0.1)
    fig.savefig(os.path.join(FIG, "fig3_lines.png"), dpi=160)
    plt.close(fig)


def fig_players():
    py = pd.read_csv(os.path.join(OUT, "players_year.csv"))
    pp = pd.read_csv(os.path.join(OUT, "players_panel.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.3))
    ax = axes[0]
    shade(ax)
    sub = py[(py.depth == 4) & (py.year >= 2013)]
    ax.plot(sub.year + 0.5, sub["within"] * 100, color=SLOT[0], marker="o", ms=4)
    ax.plot(sub.year + 0.5, sub["between"] * 100, color=SLOT[1], marker="o", ms=4)
    ax.set_ylabel("% of game pairs identical after 4 plies")
    ax.set_xlim(2013.2, 2026.9)
    ax.set_ylim(0, None)
    label_ends(ax, [("same White player", sub["within"].iloc[-1] * 100, SLOT[0]),
                    ("different players", sub["between"].iloc[-1] * 100, SLOT[1])])
    ax.set_title("Elite 2600+: repeat rates", loc="left")
    ax = axes[1]
    pan = pp.dropna(subset=["diff"])
    x = np.arange(len(pan))
    ax.bar(x, pan["diff"] * 100, color=SLOT[0], width=0.6)
    ax.errorbar(x, pan["diff"] * 100, yerr=[(pan["diff"] - pan["lo"]) * 100, (pan["hi"] - pan["diff"]) * 100],
                fmt="none", ecolor=INK2, lw=1, capsize=3)
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xticks(x, pan.depth.astype(int).astype(str))
    ax.set_xlabel("depth (plies)")
    ax.set_ylabel("change in self-repeat rate, pct points")
    ax.set_title("Same {} players, 2021-25 vs 2013-17".format(int(pan.players.iloc[0])), loc="left")
    ax.grid(axis="x", visible=False)
    fig.subplots_adjust(left=0.06, right=0.97, wspace=0.55, top=0.88, bottom=0.13)
    fig.savefig(os.path.join(FIG, "fig4_players.png"), dpi=160)
    plt.close(fig)


def fig_placebo():
    pl = pd.read_csv(os.path.join(OUT, "placebo.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.8), sharey=True)
    for ax, (band, title) in zip(axes, [("2600+", "OTB elite 2600+"),
                                        ("1800-2099 minus elite", "Gap: Lichess blitz 1800-2099 minus elite")]):
        sub = pl[(pl.band == band) & (pl.depth == 4)]
        ax.axhspan(-1.96, 1.96, color="#efeee9", lw=0)
        ax.plot(sub.T0, sub.jump_t, color=SLOT[0], marker="o", ms=3, lw=1.5)
        for name, m in EVENTS.items():
            ax.axvline(ev_t(m), color=MUTED, lw=0.8, ls=(0, (3, 3)))
        ax.set_title(title + ", 4 plies", loc="left")
        ax.set_xlabel("assumed break date")
    axes[0].set_ylabel("t statistic, level jump")
    fig.text(0.01, 0.01, "Shaded: |t| < 1.96. Dashed: the three engine dates. A real effect would peak at "
             "those dates, not elsewhere.", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(os.path.join(FIG, "fig5_placebo.png"), dpi=160)
    plt.close(fig)


def main():
    os.makedirs(FIG, exist_ok=True)
    cells = pd.read_parquet(os.path.join(OUT, "cells.parquet"))
    era = pd.read_csv(os.path.join(OUT, "era.csv"))
    fig_series(cells)
    fig_heatmap(era)
    fig_lines()
    fig_players()
    fig_placebo()
    print("figures written to", FIG)


if __name__ == "__main__":
    main()
