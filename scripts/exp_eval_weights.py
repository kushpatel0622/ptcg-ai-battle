"""Eval-weight sweep on the deploy base config (plies=2, meta opp, samples=1).

The 2-ply delta eval is:
    w_prize*(prizes taken - given) + w_dmg*(damage dealt) + w_hp*(my board HP) +/- WIN
with defaults w_prize=1000, w_dmg=2, w_hp=1, override_margin=20. Only the ratios
to w_prize and the margin matter. This sweep tests whether re-weighting the board
/ damage terms or the override margin beats the default, measured vs the heuristic
across 3 seeds (n=360). Given the unseeded-RNG noise (+-4pt @ n=360), only a
multi-seed-consistent gain of >~3pt over default counts; otherwise weights don't
matter and we keep the simple default.

Run:  python scripts/exp_eval_weights.py
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Config name -> kwargs layered on the deploy base (plies=2, opp_model, samples=1).
CONFIGS = {
    "D-default":  dict(),                      # w_dmg=2, w_hp=1, margin=20
    "HP3":        dict(w_hp=3),                # weight the 2-ply defensive signal more
    "HP8":        dict(w_hp=8),                # much more defense
    "DMG10":      dict(w_dmg=10),              # weight aggression (damage dealt) more
    "M100":       dict(override_margin=100),   # trust the heuristic prior more
    "LEAN":       dict(w_dmg=0, w_hp=0),       # prize + win only (do board terms help?)
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
    starmie = named_deck("mega_starmie_ex")
    kw = dict(plies=2, opp_model=starmie, samples=1)
    kw.update(CONFIGS[spec])
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
    return tot, (tot[0] / dec if dec else 0.0), seed_rates


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=12)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("-n", type=int, default=120)
    args = ap.parse_args()

    print(f"=== Eval-weight sweep vs heuristic (deploy base, n={args.n}x{len(args.seeds)} seeds) ===\n")
    print(f"{'config':<12} {'vs heur':>8}  {'record':>13}  {'per-seed':>13}  time")
    print("-" * 60)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for spec in CONFIGS:
            t0 = time.perf_counter()
            tot, wr, sr = run_matchup(ex, spec, "heur", args.seeds, args.n, args.chunk)
            wall = time.perf_counter() - t0
            ps = " ".join(f"{r:.0%}" for r in sr)
            print(f"{spec:<12} {wr:>7.1%}  {f'{tot[0]}-{tot[1]} (e{tot[3]})':>13}  "
                  f"{ps:>13}  [{wall:.0f}s]")
    print("\nKeep a non-default weighting only if it beats D-default by >~3pt on ALL seeds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
