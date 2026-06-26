"""Counterfactual test: would the deck-switch method find a >70% deck WITHOUT the
replay decks — i.e. from our own DESIGNED (Claude/Sakana) pool?

Screens designed, non-replay decks (Stage-2 combos the heuristic is known to
mispilot + others) with our 1-ply search vs the heuristic mirror, with a 95%
lower bound. If any clears ~70%, the method didn't depend on the replay list.

Run:  python scripts/exp_designed_screen.py
"""
from __future__ import annotations

import argparse
import math
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# All designed (non-replay) decks. Stage-2 combos first (most likely mispiloted).
DECKS = ["gardevoir_psychic", "charizard_fire", "dragapult_spread", "greninja_tempo",
         "metal_archaludon", "single_prize_control", "starmie_aggro", "fighting_pivot",
         "lightning_counter", "dual_mega_water"]


def _run_chunk(args):
    deck_name, n, seed = args
    import engine  # noqa: F401
    from baselines.heuristic_agent import heuristic_agent
    from engine.decks import named_deck
    from engine.harness import play_match
    from rl.search_teacher import SearchTeacher
    random.seed(seed)
    deck = named_deck(deck_name)
    a = SearchTeacher(deck=deck, rng=random.Random(seed), plies=1)
    res = play_match(a, heuristic_agent, deck, deck, n_games=n)
    return res["wins_a"], res["wins_b"], res["draws"], res["errors"]


def _lb(wins, dec, z=1.645):
    if not dec:
        return 0.0
    p = wins / dec
    half = z * math.sqrt(p * (1 - p) / dec + z * z / (4 * dec * dec))
    return (p + z * z / (2 * dec) - half) / (1 + z * z / dec)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=12)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4])
    args = ap.parse_args()

    print(f"=== DESIGNED (non-replay) decks: 1-ply search vs heuristic, "
          f"n={120*len(args.seeds)} ===\n")
    print(f"{'deck':<22} {'win%':>6} {'lb95':>6}  {'record':>13}  time")
    print("-" * 58)
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for deck_name in DECKS:
            t0 = time.perf_counter()
            tot = [0, 0, 0]
            for seed in args.seeds:
                jobs, remaining, k = [], 120, 0
                while remaining > 0:
                    c = min(args.chunk, remaining)
                    jobs.append((deck_name, c, seed * 1000 + k))
                    remaining -= c
                    k += 1
                for r in ex.map(_run_chunk, jobs):
                    tot[0] += r[0]; tot[1] += r[1]; tot[2] += r[3]
            dec = tot[0] + tot[1]
            wr = tot[0] / dec if dec else 0.0
            lb = _lb(tot[0], dec)
            rows.append((deck_name, wr, lb))
            star = "  >70 LB!" if lb > 0.70 else ("  >70 pt" if wr > 0.70 else "")
            print(f"{deck_name:<22} {wr:>5.1%} {lb:>5.1%}  {f'{tot[0]}-{tot[1]} (e{tot[2]})':>13}  "
                  f"[{time.perf_counter()-t0:.0f}s]{star}")
    print("\nBest designed decks (by win%):")
    for d, wr, lb in sorted(rows, key=lambda r: -r[1])[:4]:
        print(f"  {d:<22} {wr:.1%} (lb95 {lb:.1%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
