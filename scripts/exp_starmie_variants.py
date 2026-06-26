"""Compare Mega Starmie deck variants by how much our 1-ply search beats the
heuristic piloting the same deck (the >70% benchmark).

The original mega_starmie_ex has a known flaw (4 unplayable line-less Cinderace);
mega_starmie_ex_2 is a clean dual-Mega build (8 basics) and _3 a control build.
A deck the heuristic mispilots MORE gives our search more headroom. 1-ply only
(2-ply was measured worse on these decks).

Run:  python scripts/exp_starmie_variants.py
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

DECKS = ["mega_starmie_ex", "mega_starmie_ex_2", "mega_starmie_ex_3", "dual_mega_water"]


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


def _wilson_lb(wins, dec, z=1.645):
    if not dec:
        return 0.0
    p = wins / dec
    denom = 1 + z * z / dec
    half = z * math.sqrt(p * (1 - p) / dec + z * z / (4 * dec * dec))
    return (p + z * z / (2 * dec) - half) / denom


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=12)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5, 6])
    args = ap.parse_args()

    print(f"=== Deck variants: 1-ply search vs heuristic (mirror), "
          f"n=120 x {len(args.seeds)} = {120*len(args.seeds)} ===\n")
    print(f"{'deck':<20} {'win%':>6} {'lb95':>6}  {'record':>13}  time")
    print("-" * 56)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for deck_name in DECKS:
            t0 = time.perf_counter()
            tot = [0, 0, 0, 0]
            for seed in args.seeds:
                jobs, remaining, k = [], 120, 0
                while remaining > 0:
                    c = min(args.chunk, remaining)
                    jobs.append((deck_name, c, seed * 1000 + k))
                    remaining -= c
                    k += 1
                for r in ex.map(_run_chunk, jobs):
                    tot[0] += r[0]; tot[1] += r[1]; tot[2] += r[2]; tot[3] += r[3]
            dec = tot[0] + tot[1]
            wr = tot[0] / dec if dec else 0.0
            lb = _wilson_lb(tot[0], dec)
            star = "  >70 LB!" if lb > 0.70 else ""
            print(f"{deck_name:<20} {wr:>5.1%} {lb:>5.1%}  {f'{tot[0]}-{tot[1]} (e{tot[3]})':>13}  "
                  f"[{time.perf_counter()-t0:.0f}s]{star}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
