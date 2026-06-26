"""Final confirmation: a chosen deck's best config vs the heuristic at large n.

Parameterized by --deck. Confirms mega_starmie_ex_2 1-ply clears a robust >70%
(one-sided 95% lower bound) and checks whether the dynamic-attack (Resentful
Refrain) fix contributes on this Froslass-containing deck, and that 1-ply beats
2-ply here.

Run:  python scripts/exp_deck_confirm.py --deck mega_starmie_ex_2 --seeds 1..12
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

CONFIGS = {
    "1ply":       dict(plies=1, dynamic_attack=True),
    "1ply-nodyn": dict(plies=1, dynamic_attack=False),
    "2ply-gen":   dict(plies=2, dynamic_attack=True),
}


def _run_chunk(args):
    spec, deck_name, n, seed = args
    import engine  # noqa: F401
    from baselines.heuristic_agent import heuristic_agent
    from engine.decks import named_deck
    from engine.harness import play_match
    from rl.search_teacher import SearchTeacher
    random.seed(seed)
    deck = named_deck(deck_name)
    kw = dict(CONFIGS[spec])
    a = SearchTeacher(deck=deck, rng=random.Random(seed), samples=1, **kw)
    res = play_match(a, heuristic_agent, deck, deck, n_games=n)
    return res["wins_a"], res["wins_b"], res["draws"], res["errors"]


def _wilson_lb(wins, dec, z=1.645):
    if not dec:
        return 0.0
    p = wins / dec
    half = z * math.sqrt(p * (1 - p) / dec + z * z / (4 * dec * dec))
    return (p + z * z / (2 * dec) - half) / (1 + z * z / dec)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--decks", nargs="+", default=["mega_starmie_ex_2"])
    ap.add_argument("--seeds", type=int, nargs="+", default=list(range(1, 13)))
    ap.add_argument("--configs", nargs="+", default=["1ply", "1ply-nodyn", "2ply-gen"])
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=12)
    args = ap.parse_args()

    n_tot = 120 * len(args.seeds)
    print(f"=== MIRROR vs heuristic, n={n_tot} ({len(args.seeds)} seeds) ===\n")
    print(f"{'deck':<20} {'config':<12} {'win%':>6} {'lb95':>6}  {'record':>13}  time")
    print("-" * 72)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for deck in args.decks:
            for spec in args.configs:
                t0 = time.perf_counter()
                tot = [0, 0, 0, 0]
                for seed in args.seeds:
                    jobs, remaining, k = [], 120, 0
                    while remaining > 0:
                        c = min(args.chunk, remaining)
                        jobs.append((spec, deck, c, seed * 1000 + k))
                        remaining -= c
                        k += 1
                    for r in ex.map(_run_chunk, jobs):
                        tot[0] += r[0]; tot[1] += r[1]; tot[2] += r[2]; tot[3] += r[3]
                dec = tot[0] + tot[1]
                wr = tot[0] / dec if dec else 0.0
                lb = _wilson_lb(tot[0], dec)
                star = "  >80!" if lb > 0.80 else ("  >70 LB" if lb > 0.70 else "")
                print(f"{deck:<20} {spec:<12} {wr:>5.1%} {lb:>5.1%}  "
                      f"{f'{tot[0]}-{tot[1]} (e{tot[3]})':>13}  [{time.perf_counter()-t0:.0f}s]{star}")
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
