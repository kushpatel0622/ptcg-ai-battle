"""Compare the 1-ply vs 2-ply SearchTeacher: win-rate AND per-move latency.

Win-rate is measured vs the heuristic on the dual_mega_water mirror (the same
benchmark as test_search_teacher.py). Latency matters because the Kaggle grader
enforces a PER-MOVE time limit, so we report both the average and the MAX single
decision time for the search agent (a single slow MAIN decision is what risks a
timeout, not the average).

Run:
    python scripts/compare_search_plies.py -n 40            # 1-ply & 2-ply vs heuristic
    python scripts/compare_search_plies.py -n 40 --h2h      # also 2-ply vs 1-ply head-to-head
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine  # noqa: E402,F401
from baselines.heuristic_agent import heuristic_agent  # noqa: E402
from engine.decks import named_deck  # noqa: E402
from engine.harness import play_match  # noqa: E402
from rl.search_teacher import SearchTeacher  # noqa: E402


class Timed:
    """Wrap an agent to record call count, total and max single-call time."""

    def __init__(self, fn, name):
        self.fn = fn
        self.name = name
        self.calls = 0
        self.total = 0.0
        self.max = 0.0

    def __call__(self, obs):
        t0 = time.perf_counter()
        out = self.fn(obs)
        dt = time.perf_counter() - t0
        self.total += dt
        self.max = max(self.max, dt)
        self.calls += 1
        return out

    def report(self):
        avg = 1000.0 * self.total / self.calls if self.calls else 0.0
        return (f"{self.name}: {self.calls} decisions, "
                f"avg {avg:.1f} ms/move, max {1000.0 * self.max:.1f} ms")


def run(deck, plies, games, seed):
    teacher = Timed(SearchTeacher(deck=deck, rng=random.Random(seed), plies=plies),
                    f"search(plies={plies})")
    res = play_match(teacher, heuristic_agent, deck, deck, n_games=games)
    return res, teacher


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--h2h", action="store_true", help="also play 2-ply vs 1-ply")
    args = ap.parse_args()

    deck = named_deck("dual_mega_water")

    print(f"=== SearchTeacher win-rate & latency (dual_mega_water mirror, "
          f"{args.games} games each) ===\n")

    for plies in (1, 2):
        random.seed(args.seed)
        t0 = time.perf_counter()
        res, timed = run(deck, plies, args.games, args.seed)
        wall = time.perf_counter() - t0
        print(f"--- plies={plies} vs heuristic ---")
        print(f"  win-rate (decisive): {res['winrate_a']:.1%}  "
              f"({res['wins_a']}-{res['wins_b']}, draws {res['draws']}, "
              f"errors {res['errors']})")
        print(f"  {timed.report()}")
        print(f"  wall: {wall:.1f}s\n")

    if args.h2h:
        random.seed(args.seed)
        a2 = Timed(SearchTeacher(deck=deck, rng=random.Random(args.seed), plies=2), "2-ply")
        a1 = SearchTeacher(deck=deck, rng=random.Random(args.seed + 1), plies=1)
        res = play_match(a2, a1, deck, deck, n_games=args.games)
        print("--- 2-ply vs 1-ply (head-to-head) ---")
        print(f"  2-ply win-rate (decisive): {res['winrate_a']:.1%}  "
              f"({res['wins_a']}-{res['wins_b']}, draws {res['draws']}, "
              f"errors {res['errors']})")
        print(f"  {a2.report()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
