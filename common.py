"""Shared helpers: SAN tokenising, time-control classes, rating bands, paths."""
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "out")
FIG = os.path.join(ROOT, "figures")

PLIES = 20  # opening prefix kept per game

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# Engine milestones used as candidate breakpoints (month the tool became usable).
EVENTS = {
    "AlphaZero paper": "2017-12",
    "Leela wins TCEC": "2019-05",
    "Stockfish 12 NNUE": "2020-09",
}

_COMMENT = re.compile(r"\{[^}]*\}|;[^\n]*")
_VARIATION = re.compile(r"\([^()]*\)")
_MOVENUM = re.compile(r"\d+\.(?:\.\.)?")
_RESULT = {"1-0", "0-1", "1/2-1/2", "*"}


def san_plies(movetext, n=PLIES):
    """First n plies of a PGN movetext as normalised SAN tokens.

    Drops comments, variations, move numbers, NAGs, annotation glyphs and
    check marks, and writes castling with letters, so the same move reads the
    same in a Lichess dump and in a TWIC file.
    """
    s = _COMMENT.sub(" ", movetext)
    while "(" in s:
        t = _VARIATION.sub(" ", s)
        if t == s:
            break
        s = t
    s = _MOVENUM.sub(" ", s)
    out = []
    for tok in s.split():
        if tok in _RESULT or tok[0] == "$":
            continue
        tok = tok.rstrip("+#!?")
        if not tok:
            continue
        if tok[0] == "0":
            tok = tok.replace("0", "O")
        out.append(tok)
        if len(out) == n:
            break
    return out


def lichess_speed(tc):
    """Lichess speed class from a TimeControl tag such as '180+2'."""
    if not tc or "+" not in tc:
        return None
    base, inc = tc.split("+", 1)
    try:
        est = int(base) + 40 * int(inc)
    except ValueError:
        return None
    if est < 29:
        return "ultrabullet"
    if est < 180:
        return "bullet"
    if est < 480:
        return "blitz"
    if est < 1500:
        return "rapid"
    return "classical"


# Lichess rating bands on the mean rating of the two players.
LICHESS_BANDS = [(0, 1200, "<1200"), (1200, 1500, "1200-1499"), (1500, 1800, "1500-1799"),
                 (1800, 2100, "1800-2099"), (2100, 2400, "2100-2399"), (2400, 4000, "2400+")]


def lichess_band(mean_elo):
    for lo, hi, name in LICHESS_BANDS:
        if lo <= mean_elo < hi:
            return name
    return None


_FAST = re.compile(r"rapid|blitz|bullet|armageddon|blindfold|960|fischer|freestyle|"
                   r"speed|titled|banter|bughouse|chess ?9lx|chess ?24|playoff|tiebreak|"
                   r"tie-break|tb\b|online|lichess|chess\.com|champions chess|"
                   r"meltwater|bullet|hyper|arena|\bq?ccc\b|pro chess league|esports|"
                   r"blind|basque|simul|\bbl\b|lindores", re.I)
_ONLINE_SITE = re.compile(r"chess\.com|lichess|\bINT\b|online|chess24|icc\b|playchess", re.I)


def twic_kind(event, site, event_type="", rnd=""):
    """'classical' for over-the-board standard play, else 'online' or 'fast'.

    Knockout events (World Cups) play two classical games per match; TWIC
    numbers tiebreak games 3 and up within the round ('2.3', '2.4', ...).
    """
    if _ONLINE_SITE.search(site or ""):
        return "online"
    if _FAST.search(event or ""):
        return "fast"
    if "k.o." in (event_type or "") or "world cup" in (event or "").lower():
        parts = (rnd or "").split(".")
        if len(parts) == 2 and parts[1].isdigit() and int(parts[1]) >= 3:
            return "fast"
    return "classical"
