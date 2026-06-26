"""Does an agent on the mega_starmie_ex deck clear >70% vs the heuristic?

dual_mega_water tops out at ~68% vs the heuristic (a structural mirror ceiling),
and it LOSES to mega_starmie_ex head-to-head. The hypothesis: the heuristic
mispilots the (harder) mega_starmie_ex deck — Nebula Beam's 3-energy cost,
evolution timing — so our search beats heuristic-piloted mega_starmie_ex by more.
Quick n=60 showed 1-ply at 73%. This confirms it at large n with a one-sided
lower bound, and checks whether 1-ply or 2-ply is better on this deck.

Run:  python scripts/exp_starmie_deck.py
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

DECK = "mega_starmie_ex"
CONFIGS = {
    "1ply":     dict(plies=1),
    "2ply-gen": dict(plies=2),
    "2ply-meta": dict(plies=2, use_opp_model=True),
}


def _build(spec, seed):
    import engine  # noqa: F401
    from baselines.heuristic_agent import heuristic_agent
    from engine.decks import named_deck
    from rl.search_teacher import SearchTeacher
    deck = named_deck(DECK)
    if spec == "heur":
        return heuristic_agent, deck
    cfg = dict(CONFIGS[spec])
    kw = dict(plies=cfg["plies"], samples=1)
    if cfg.get("use_opp_model"):
        kw["opp_model"] = named_deck(DECK)
    return SearchTeacher(deck=deck, rng=random.Random(seed), **kw), deck


def _run_chunk(args):
    specA, specB, n, seed = args
    import engine  # noqa: F401
    from engine.harness import play_match
    random.seed(seed)
    a, deck = _build(specA, seed)
    b, _ = _build(specB, seed + 10_000)
    res = play_match(a, b, deck, deck, n_games=n)
    return res["wins_a"], res["wins_b"], res["draws"], res["errors"]


def _wilson_lb(wins, dec, z=1.645):
    if not dec:
        return 0.0
    p = wins / dec
    denom = 1 + z * z / dec
    center = p + z * z / (2 * dec)
    half = z * math.sqrt(p * (1 - p) / dec + z * z / (4 * dec * dec))
    return (center - half) / denom


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
    return tot, (tot[0] / dec if dec else 0.0), seed_rates, _wilson_lb(tot[0], dec)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=12)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    ap.add_argument("--only", nargs="+", default=None, help="restrict to these configs")
    args = ap.parse_args()

    specs = args.only if args.only else list(CONFIGS)
    print(f"=== {DECK} MIRROR vs heuristic (n=120 x {len(args.seeds)} seeds = "
          f"{120*len(args.seeds)}) ===\n")
    print(f"{'config':<12} {'win%':>6} {'lb95':>6}  {'record':>13}  {'per-seed':>26}  time")
    print("-" * 82)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for spec in specs:
            t0 = time.perf_counter()
            tot, wr, sr, lb = run_matchup(ex, spec, "heur", args.seeds, 120, args.chunk)
            ps = " ".join(f"{r:.0%}" for r in sr)
            star = "  >70 LB!" if lb > 0.70 else ""
            print(f"{spec:<12} {wr:>5.1%} {lb:>5.1%}  {f'{tot[0]}-{tot[1]}':>13}  {ps:>22}  "
                  f"[{time.perf_counter()-t0:.0f}s]{star}")
    print("\n>70% achieved if lb95 > 70.0 (one-sided 95% lower bound).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
