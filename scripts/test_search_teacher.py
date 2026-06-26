"""Validate the SearchTeacher beats the heuristic on dual_mega_water.

Success criterion: SearchTeacher win-rate > 55% over >= 20 games, both piloting
the dual_mega_water deck.

Run:
    python scripts/test_search_teacher.py            # 20 games
    python scripts/test_search_teacher.py -n 40      # more games
"""
from __future__ import annotations

import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from baselines.heuristic_agent import heuristic_agent  # noqa: E402
from engine.decks import named_deck  # noqa: E402
from engine.harness import play_match  # noqa: E402
from rl.search_teacher import SearchTeacher  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    random.seed(args.seed)
    deck = named_deck("dual_mega_water")
    teacher = SearchTeacher(deck=deck, rng=random.Random(args.seed))

    res = play_match(teacher, heuristic_agent, deck, deck, n_games=args.games)

    print("=== SearchTeacher vs heuristic (dual_mega_water mirror) ===")
    print(f"games:     {res['n']}")
    print(f"wins_a (SearchTeacher): {res['wins_a']}")
    print(f"wins_b (heuristic):     {res['wins_b']}")
    print(f"draws:     {res['draws']}")
    print(f"errors:    {res['errors']}")
    print(f"WIN-RATE (SearchTeacher, decisive games): {res['winrate_a']:.1%}")
    gate = res["winrate_a"] > 0.55
    print(f"GATE (>55%): {'PASS' if gate else 'FAIL'}")
    return 0 if gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
