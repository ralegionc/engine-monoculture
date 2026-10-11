"""Who is narrowing: each player, or the field as a whole?

Among over-the-board classical games between two 2600+ players, take every
pair of games in a year and ask whether they share their first d plies.

  within    both games have the same player with White (personal repertoire
            repeating itself)
  between   different White players (two players landing on the same line)

The overall collision rate is a mix of the two, so a falling diversity can come
from players repeating themselves more, from players copying each other more,
or from the mix shifting. Engine preparation predicts 'between' should rise:
different people consulting the same oracle reach the same lines.

Also a fixed panel: the same players' White repertoires before (2013-2017) and
after (2021-2025), paired within player, so changes in who is in the 2600+
group cannot drive the result.

Output: out/players_year.csv, out/players_panel.csv
"""
import os

import numpy as np
import pandas as pd

from common import OUT
from entropy import prefix_codes, twic_games

DEPTHS = [2, 4, 6, 8, 10, 12, 16]


def pair_counts(codes, player):
    """Matching pairs overall and within player, for one depth."""
    df = pd.DataFrame({"c": codes, "p": player})
    n_all = df.groupby("c").size().to_numpy()
    n_wp = df.groupby(["p", "c"]).size().to_numpy()
    n_p = df.groupby("p").size().to_numpy()
    N = len(df)
    match_all = (n_all * (n_all - 1)).sum() / 2
    match_within = (n_wp * (n_wp - 1)).sum() / 2
    pairs_all = N * (N - 1) / 2
    pairs_within = (n_p * (n_p - 1)).sum() / 2
    return match_all, match_within, pairs_all, pairs_within


def yearly(df):
    rows = []
    codes = prefix_codes(df["moves"])
    for year, idx in df.groupby("year").indices.items():
        pl = df["wid"].to_numpy()[idx]
        for d in DEPTHS:
            ma, mw, pa, pw = pair_counts(codes[idx, d - 1], pl)
            rows.append({"year": year, "depth": d, "games": len(idx),
                         "players": len(set(pl)),
                         "overall": ma / pa, "within": mw / pw if pw else np.nan,
                         "between": (ma - mw) / (pa - pw),
                         "share_within_pairs": pw / pa})
    return pd.DataFrame(rows)


def panel(df, pre=("2013", "2017"), post=("2021", "2025"), min_games=15):
    era = np.where(df.year.between(*pre), "pre", np.where(df.year.between(*post), "post", None))
    df = df.assign(era=era).dropna(subset=["era"])
    cnt = df.groupby(["wid", "era"]).size().unstack()
    keep = cnt[(cnt["pre"] >= min_games) & (cnt["post"] >= min_games)].index
    df = df[df.wid.isin(keep)].reset_index(drop=True)
    codes = prefix_codes(df["moves"])
    rows = []
    for (pid, e), idx in df.groupby(["wid", "era"]).indices.items():
        for d in DEPTHS:
            c = np.bincount(pd.factorize(codes[idx, d - 1])[0]).astype(float)
            n = c.sum()
            rows.append({"wid": pid, "era": e, "depth": d, "games": n,
                         "repeat": (c * (c - 1)).sum() / (n * (n - 1))})
    per = pd.DataFrame(rows).pivot_table(index=["wid", "depth"], columns="era", values="repeat").reset_index()
    out = []
    rng = np.random.default_rng(0)
    for d, g in per.groupby("depth"):
        diff = (g["post"] - g["pre"]).to_numpy()
        boots = [rng.choice(diff, len(diff)).mean() for _ in range(2000)]
        out.append({"depth": d, "players": len(diff), "pre": g["pre"].mean(), "post": g["post"].mean(),
                    "diff": diff.mean(), "lo": np.percentile(boots, 2.5), "hi": np.percentile(boots, 97.5),
                    "share_up": (diff > 0).mean()})
    # the field among the same players: between-player matches, pre vs post
    for e in ["pre", "post"]:
        sub = df[df.era == e].reset_index(drop=True)
        cs = prefix_codes(sub["moves"])
        for d in DEPTHS:
            ma, mw, pa, pw = pair_counts(cs[:, d - 1], sub["wid"].to_numpy())
            out.append({"depth": d, "players": len(keep), "era": e, "between": (ma - mw) / (pa - pw)})
    return pd.DataFrame(out)


def main():
    df = twic_games()
    df = df[(df.kind == "classical") & (df.band == "2600+")].copy()
    df["year"] = df["month"].str[:4]
    df["wid"] = df["wfide"].where(df["wfide"].str.len() > 0, df["white"])
    df = df[df.year.between("2013", "2026")].reset_index(drop=True)
    yearly(df).to_csv(os.path.join(OUT, "players_year.csv"), index=False)
    panel(df).to_csv(os.path.join(OUT, "players_panel.csv"), index=False)
    print("wrote players_year.csv, players_panel.csv")


if __name__ == "__main__":
    main()
