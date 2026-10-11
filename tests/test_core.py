import os
import sys

import numpy as np
import pandas as pd
import zstandard

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common import lichess_band, lichess_speed, san_plies, twic_kind  # noqa: E402
from entropy import cell_stats, prefix_codes  # noqa: E402
from fetch_lichess import decode_slice, parse_game, split_games  # noqa: E402


def test_san_plies_strips_annotations():
    mt = ("1. e4 { [%eval 0.2] [%clk 0:03:00] } 1... c5?! 2. Nf3 $1 (2. c3 d5) 2... d6 "
          "3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6 6. Bg5+ e6 7. 0-0-0 Qb6# 1-0")
    assert san_plies(mt) == ["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "a6",
                             "Bg5", "e6", "O-O-O", "Qb6"]
    assert san_plies(mt, 3) == ["e4", "c5", "Nf3"]


def test_speed_and_band():
    assert lichess_speed("60+0") == "bullet"
    assert lichess_speed("180+2") == "blitz"
    assert lichess_speed("600+0") == "rapid"
    assert lichess_speed("1800+30") == "classical"
    assert lichess_speed("-") is None
    assert lichess_band(1499.5) == "1200-1499"
    assert lichess_band(2600) == "2400+"


def test_twic_kind():
    assert twic_kind("Titled Tue 1st Jul Early", "chess.com INT") == "online"
    assert twic_kind("SuperUnited CRO Rapid 2025", "Zagreb CRO") == "fast"
    assert twic_kind("Tata Steel Masters", "Wijk aan Zee NED") == "classical"
    assert twic_kind("FIDE World Bl Team Final", "Almaty KAZ") == "fast"
    assert twic_kind("FIDE World Cup 2023", "Baku AZE", "k.o.", "2.2") == "classical"
    assert twic_kind("FIDE World Cup 2023", "Baku AZE", "k.o.", "2.3") == "fast"


def test_prefix_codes_nest():
    moves = pd.Series([" ".join(["e4", "e5"] + ["x"] * 18),
                       " ".join(["e4", "c5"] + ["x"] * 18),
                       " ".join(["e4", "e5"] + ["x"] * 18),
                       " ".join(["d4", "e5"] + ["x"] * 18)])
    c = prefix_codes(moves)
    assert c[0, 0] == c[1, 0] == c[2, 0] != c[3, 0]
    assert c[0, 1] == c[2, 1] != c[1, 1]
    assert c[3, 1] not in (c[0, 1], c[1, 1])  # same 2nd move, different 1st


def test_cell_stats_uniform_and_collision():
    h_plug, h_cs, s2, h2, k = cell_stats(np.array([5, 5, 5, 5]))
    assert abs(h_plug - 2.0) < 1e-12 and k == 4
    assert abs(s2 - 4 * 20 / (20 * 19)) < 1e-12
    # the collision estimator is unbiased: average over many samples ~ sum p^2
    rng = np.random.default_rng(0)
    p = np.array([0.5, 0.3, 0.15, 0.05])
    vals = []
    for _ in range(4000):
        x = np.bincount(rng.choice(4, 30, p=p), minlength=4)
        vals.append(cell_stats(x[x > 0])[2])
    assert abs(np.mean(vals) - (p ** 2).sum()) < 0.004


def test_chao_shen_less_biased_than_plugin():
    rng = np.random.default_rng(1)
    p = rng.dirichlet(np.ones(300))
    true = -(p * np.log2(p)).sum()
    plug, cs = [], []
    for _ in range(200):
        x = np.bincount(rng.choice(300, 200, p=p))
        x = x[x > 0]
        a, b, *_ = cell_stats(x)
        plug.append(a)
        cs.append(b)
    assert abs(np.mean(cs) - true) < abs(np.mean(plug) - true)


def _pgn(i):
    return ('[Event "Rated Blitz game"]\n[UTCDate "2020.01.0{}"]\n[WhiteElo "1500"]\n'
            '[BlackElo "1600"]\n[TimeControl "180+0"]\n[Termination "Normal"]\n[Result "1-0"]\n\n'
            '1. e4 {{ [%clk 0:03:00] }} 1... e5 2. Nf3 Nc6 3. Bb5 a6 1-0\n\n').format(i % 9 + 1)


def test_decode_slice_from_mid_file():
    cctx = zstandard.ZstdCompressor()
    frames = [cctx.compress("".join(_pgn(i) for i in range(j * 50, j * 50 + 50)).encode())
              for j in range(6)]
    blob = b"".join(frames)
    cut = len(frames[0]) // 2  # start mid-frame: decoding must skip to frame 2
    text = decode_slice(blob[cut:])
    games = split_games(text)
    assert len(games) >= 4 * 50 - 2
    r = parse_game(games[0])
    assert r[1] == "blitz" and r[3] == 1500 and r[8] == "e4 e5 Nf3 Nc6 Bb5 a6"
    whole = split_games(decode_slice(blob, from_start=True), whole_file=True)
    assert len(whole) == 300


def test_cluster_bootstrap_centred():
    """Resampled H2 must sit around the point estimate even when matches are rare."""
    from robustness import h2_boot
    rng = np.random.default_rng(3)
    codes = rng.integers(0, 20000, 6000)          # nearly all sequences unique
    cluster = np.repeat(np.arange(60), 100)
    point, draws = h2_boot(codes, cluster, rng, boot=200)
    assert abs(np.median(draws) - point) < 0.1
