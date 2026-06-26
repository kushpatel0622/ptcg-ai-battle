"""Decisive test of the dynamic-attack (Resentful Refrain) exploit.

The heuristic ranks attacks by db.attack_damage, which is 0 for Mega Froslass
ex's Resentful Refrain (true damage = 50 x opponent hand size), so it never plays
it. The agent now ranks ATTACK options by true dynamic damage (dynamic_attack).
This battery measures the gain at LARGE n (the +-4pt RNG noise needs >=600 games
and a head-to-head to beat). Reports a one-sided lower bound on the win-rate.

Run:  python scripts/exp_dynamic_attack.py
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

# config -> kwargs on base (plies=2, samples=1)
CONFIGS = {
    "base":    dict(opp_model=True, dynamic_attack=False),  # current champion
    "dyn":     dict(opp_model=True, dynamic_attack=True),   # + Refrain fix
    "dyn-gen": dict(opp_model=False, dynamic_attack=True),  # Refrain fix, generic opp (simpler)
}


def _build(spec, seed):
    import engine  # noqa: F401
    from baselines.heuristic_agent import heuristic_agent
    from engine.decks import named_deck
    from rl.search_teacher import SearchTeacher

    deck = named_deck("dual_mega_water")
    if spec == "heur":
        return heuristic_agent, deck
    rng = random.Random(seed)
    cfg = dict(CONFIGS[spec])
    kw = dict(plies=2, samples=1, dynamic_attack=cfg["dynamic_attack"])
    if cfg["opp_model"]:
        kw["opp_model"] = named_deck("mega_starmie_ex")
    return SearchTeacher(deck=deck, rng=rng, **kw), deck


def _run_chunk(args):
    specA, specB, n, seed = args
    import engine  # noqa: F401
    from engine.harness import play_match
    random.seed(seed)
    a, deck = _build(specA, seed)
    b, _ = _build(specB, seed + 10_000)
    res = play_match(a, b, deck, deck, n_games=n)
    return res["wins_a"], res["wins_b"], res["draws"], res["errors"]


def run_matchup(ex, specA, specB, seeds, n, chunk):
    tot = [0, 0, 0, 0]
    seed_rates = []
    for seed in seeds:
        jobs, remaining, k = [], n, 0
        while remaining > 0:
            c = min(chunk, remaining)
            jobs.append((specA, specB, c, seed * 1000 + k))
            remaining -= c
            k += 1
        results = list(ex.map(_run_chunk, jobs))
        sa = sum(r[0] for r in results); sb = sum(r[1] for r in results)
        tot[0] += sa; tot[1] += sb
        tot[2] += sum(r[2] for r in results); tot[3] += sum(r[3] for r in results)
        seed_rates.append(sa / (sa + sb) if (sa + sb) else 0.0)
    dec = tot[0] + tot[1]
    wr = tot[0] / dec if dec else 0.0
    # Wilson one-sided lower 95% bound on the win-rate.
    lb = 0.0
    if dec:
        z = 1.645
        p, nn = wr, dec
        denom = 1 + z * z / nn
        center = p + z * z / (2 * nn)
        half = z * math.sqrt(p * (1 - p) / nn + z * z / (4 * nn * nn))
        lb = (center - half) / denom
    return tot, wr, seed_rates, lb


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=12)
    args = ap.parse_args()

    print("=== Dynamic-attack (Resentful Refrain) decisive test ===\n")
    print(f"{'matchup':<22} {'win%':>6} {'lb95':>6}  {'record':>13}  {'per-seed':>22}  time")
    print("-" * 84)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for spec in ("base", "dyn", "dyn-gen"):
            t0 = time.perf_counter()
            tot, wr, sr, lb = run_matchup(ex, spec, "heur", [1, 2, 3, 4, 5], 120, args.chunk)
            ps = " ".join(f"{r:.0%}" for r in sr)
            print(f"{spec+' vs heur':<22} {wr:>5.1%} {lb:>5.1%}  {f'{tot[0]}-{tot[1]}':>13}  "
                  f"{ps:>22}  [{time.perf_counter()-t0:.0f}s]")

        print("\n--- head-to-head: is the Refrain fix actually a better player? ---")
        t0 = time.perf_counter()
        tot, wr, sr, lb = run_matchup(ex, "dyn", "base", [1, 2, 3, 4], 120, args.chunk)
        ps = " ".join(f"{r:.0%}" for r in sr)
        print(f"{'dyn vs base':<22} {wr:>5.1%} {lb:>5.1%}  {f'{tot[0]}-{tot[1]}':>13}  {ps:>22}  "
              f"[{time.perf_counter()-t0:.0f}s]")
    print("\n>70% claim needs win% lb95 > 70 (one-sided). Fix is real if dyn vs base lb95 > 50.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
