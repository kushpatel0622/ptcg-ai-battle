"""Experiment battery for the deeper (2-ply) SearchTeacher + opponent models.

Direct head-to-head matchups give the most signal per game, so the key question
— "is the deeper agent actually stronger?" — is answered by playing the variants
against each other, not just against a third party. We also keep the standing
vs-heuristic benchmark for continuity with test_search_teacher.py.

Variants:
  1ply        — legacy deployed agent (horizon = end of my turn)
  2ply-gen    — 2-ply, generic (Staryu + Water energy) opponent fill
  2ply-meta   — 2-ply, opponent dealt from a real archetype (mega_starmie_ex)
  2ply-true   — 2-ply, opponent dealt from the actual mirror deck (upper bound)

Run:
    python scripts/exp_2ply.py -n 120
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
    def __init__(self, fn):
        self.fn, self.calls, self.total, self.max = fn, 0, 0.0, 0.0

    def __call__(self, obs):
        t0 = time.perf_counter()
        out = self.fn(obs)
        dt = time.perf_counter() - t0
        self.total += dt
        self.max = max(self.max, dt)
        self.calls += 1
        return out

    def stats(self):
        avg = 1000.0 * self.total / self.calls if self.calls else 0.0
        return avg, 1000.0 * self.max


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games", type=int, default=120)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    deck = named_deck("dual_mega_water")
    starmie = named_deck("mega_starmie_ex")

    def mk(kind, seed):
        rng = random.Random(seed)
        if kind == "1ply":
            return SearchTeacher(deck=deck, rng=rng, plies=1)
        if kind == "2ply-gen":
            return SearchTeacher(deck=deck, rng=rng, plies=2)
        if kind == "2ply-meta":
            return SearchTeacher(deck=deck, rng=rng, plies=2, opp_model=starmie)
        if kind == "2ply-true":
            return SearchTeacher(deck=deck, rng=rng, plies=2, opp_model=deck)
        if kind == "heur":
            return heuristic_agent
        raise ValueError(kind)

    # (label, kindA, kindB) — A's win-rate is what we read.
    battery = [
        ("2ply-gen  vs 1ply ", "2ply-gen", "1ply"),
        ("2ply-meta vs 1ply ", "2ply-meta", "1ply"),
        ("2ply-meta vs 2ply-gen", "2ply-meta", "2ply-gen"),
        ("2ply-meta vs heur ", "2ply-meta", "heur"),
        ("1ply     vs heur ", "1ply", "heur"),
    ]

    print(f"=== 2-ply experiment battery (dual_mega_water, {args.games} games each) ===\n")
    for label, kindA, kindB in battery:
        random.seed(args.seed)
        a = Timed(mk(kindA, args.seed))
        b = mk(kindB, args.seed + 1)
        t0 = time.perf_counter()
        res = play_match(a, b, deck, deck, n_games=args.games)
        wall = time.perf_counter() - t0
        avg, mx = a.stats()
        print(f"{label}: A win-rate {res['winrate_a']:.1%}  "
              f"({res['wins_a']}-{res['wins_b']}, draws {res['draws']}, err {res['errors']})  "
              f"| A {avg:.1f} ms/move (max {mx:.0f})  | {wall:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
