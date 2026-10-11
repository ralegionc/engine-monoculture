"""Run the pipeline end to end, or one step:  python run.py [step ...]

Steps in order: fetch_twic fetch_lichess canonicalize validate entropy breaks
players robustness figures report. Fetch steps resume where they stopped.
"""
import subprocess
import sys

STEPS = [
    ("fetch_twic", ["fetch_twic.py"]),
    ("fetch_lichess", ["fetch_lichess.py", "--k", "24", "--jobs", "3"]),
    ("canonicalize", ["canonicalize.py"]),
    ("validate", ["validate.py"]),
    ("entropy", ["entropy.py"]),
    ("breaks", ["breaks.py"]),
    ("players", ["players.py"]),
    ("robustness", ["robustness.py"]),
    ("figures", ["figures.py"]),
    ("report", ["report.py"]),
]


def main():
    want = sys.argv[1:] or [s for s, _ in STEPS]
    for name, cmd in STEPS:
        if name not in want:
            continue
        print("==", name, flush=True)
        if name == "report":
            with open("out/summary.md", "w", encoding="utf-8") as f:
                subprocess.run([sys.executable] + cmd, check=True, stdout=f)
        else:
            subprocess.run([sys.executable] + cmd, check=True)


if __name__ == "__main__":
    main()
