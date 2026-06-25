"""Use Sakana (the strongest model) to reason over the candidate deck pool and
pick the best deck(s) + suggest improvements. One reasoning call -> cheap.

This is the "Sakana finds the best deck" step. The decks it favors are then
handed to cheaper models for high-volume simulation (run_multideck_arena.py).

Run with the conda env's python:
  C:/Users/itach/miniconda3/envs/pokemon_tcg/python.exe scripts/sakana_pick_deck.py
"""
import collections
import glob
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(REPO, ".env"))

import engine  # noqa: E402,F401
from cg.api import CardType  # noqa: E402
from engine.cards import get_card_db  # noqa: E402
from engine.decks import load_deck  # noqa: E402
from llm.providers.sakana_agent import SakanaProvider  # noqa: E402

DECKS_DIR = os.path.join(REPO, "decks")


def summarize_deck(path, db) -> str:
    deck = load_deck(path)
    cnt = collections.Counter(deck)
    poke, trainer, energy = [], [], []
    basics = energy_n = 0
    for cid, n in cnt.most_common():
        c = db.card(cid)
        nm = c.name if c else f"#{cid}"
        ct = int(c.cardType) if c else -1
        if ct == CardType.POKEMON:
            stage = "Basic" if c.basic else ("St1" if c.stage1 else ("St2" if c.stage2 else "?"))
            poke.append(f"{n}x {nm}[{stage} HP{c.hp}]")
            if c.basic:
                basics += n
        elif ct in (CardType.BASIC_ENERGY, CardType.SPECIAL_ENERGY):
            energy.append(f"{n}x {nm}")
            energy_n += n
        else:
            trainer.append(f"{n}x {nm}")
    name = os.path.splitext(os.path.basename(path))[0]
    return (f"DECK {name} (Basics={basics}, Energy={energy_n}):\n"
            f"  Pokemon: {', '.join(poke)}\n"
            f"  Trainers: {', '.join(trainer)}\n"
            f"  Energy: {', '.join(energy)}")


def main() -> int:
    db = get_card_db()
    paths = sorted(glob.glob(os.path.join(DECKS_DIR, "*.csv")))
    summaries = "\n\n".join(summarize_deck(p, db) for p in paths)

    system = ("You are a world-class competitive Pokemon TCG analyst and deckbuilder. "
              "Be specific and concise; cite exact card counts.")
    user = (
        "Below are candidate 60-card decks for a Pokemon TCG AI competition. The ladder meta (from real "
        "leaderboard replays) is dominated by Mega Starmie ex Water decks (fast Staryu -> Mega Starmie ex "
        "with heavy search/draw + Crushing Hammer energy denial).\n\n"
        "Tasks:\n"
        "1. RANK these decks from strongest to weakest for competitive ladder play, weighing power AND "
        "consistency (legal, robust openings, a clear path to 6 prizes).\n"
        "2. Recommend the SINGLE best deck to commit to, and a strong #2.\n"
        "3. For your top pick, suggest 2-4 concrete improvements (specific card swaps with counts).\n\n"
        f"{summaries}"
    )

    print(f"Analyzing {len(paths)} decks with Sakana fugu-ultra...\n")
    provider = SakanaProvider(model="fugu-ultra", max_tokens=1800)
    out = provider.complete(system, user)
    print(out)

    os.makedirs(os.path.join(REPO, "data"), exist_ok=True)
    with open(os.path.join(REPO, "data", "sakana_deck_analysis.md"), "w", encoding="utf-8") as f:
        f.write(f"# Sakana deck analysis ({len(paths)} decks)\n\n{out}\n")
    print("\n[saved -> data/sakana_deck_analysis.md]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
