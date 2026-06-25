"""M0 second harness: run a game through the official kaggle_environments
"cabt" environment and render an HTML replay.

Uses a pure-dict random agent (no `cg` import) so we don't double-load the
engine DLL alongside the environment's own copy. Requires the conda env
(kaggle-environments). Run with the env's python:

  C:/Users/itach/miniconda3/envs/pokemon_tcg/python.exe scripts/smoke_kaggle.py
"""
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK_PATH = os.path.join(REPO, "submission", "deck.csv")
OUT_HTML = os.path.join(REPO, "result.html")

with open(DECK_PATH) as f:
    DECK = [int(x) for x in f.read().split() if x.strip()]


def random_agent(obs, *_):
    """obs is the raw cabt observation dict."""
    sel = obs.get("select") if isinstance(obs, dict) else None
    if not sel:  # deck selection
        return DECK
    n = len(sel["option"])
    k = min(sel.get("maxCount", 1), n)
    return random.sample(range(n), k) if k > 0 else []


def main() -> int:
    from kaggle_environments import make

    random.seed(0)
    env = make("cabt", configuration={"decks": [DECK, DECK]})
    env.run([random_agent, random_agent])

    rewards = [s.get("reward") for s in env.state]
    statuses = [s.get("status") for s in env.state]
    print(f"kaggle_environments cabt | rewards={rewards} | statuses={statuses}")

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(env.render(mode="html"))
    print(f"replay written: {OUT_HTML}")

    done = all(s == "DONE" for s in statuses)
    print("M0 kaggle_environments smoke test PASSED" if done else "WARNING: not all agents DONE")
    return 0 if done else 1


if __name__ == "__main__":
    raise SystemExit(main())
