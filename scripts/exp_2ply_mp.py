"""Multi-seed, multi-core confirmation battery for the 2-ply SearchTeacher.

The single-seed n=120 battery suggested deeper (2-ply) search is NOT better than
1-ply and may be worse. This script confirms that across several seeds and tests
the two untested rescue levers — determinization averaging (samples) and the
meta-deck opponent — by parallelising games across CPU cores.

Each matchup is split into chunks dispatched to a process pool; every worker
process gets its own cg.dll instance (the engine keeps module-global state, so
processes must not be shared with the main interpreter's games). Results are
summed across chunks and seeds.

Run:
    python scripts/exp_2ply_mp.py
    python scripts/exp_2ply_mp.py -n 120 --seeds 1 2 3 --workers 10
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _build(spec, seed):
    """Construct an agent from a spec string inside the worker process."""
    import engine  # noqa: F401  (puts submission/ on sys.path)
    from baselines.heuristic_agent import heuristic_agent
    from engine.decks import named_deck
    from rl.search_teacher import SearchTeacher

    deck = named_deck("dual_mega_water")
    if spec == "heur":
        return heuristic_agent, deck
    rng = random.Random(seed)
    if spec == "1ply":
        return SearchTeacher(deck=deck, rng=rng, plies=1), deck
    if spec == "2ply-gen":
        return SearchTeacher(deck=deck, rng=rng, plies=2), deck
    if spec == "2ply-gen-s3":
        return SearchTeacher(deck=deck, rng=rng, plies=2, samples=3), deck
    if spec == "2ply-meta":
        return SearchTeacher(deck=deck, rng=rng, plies=2, opp_model=named_deck("mega_starmie_ex")), deck
    if spec == "2ply-meta-s3":
        return SearchTeacher(deck=deck, rng=rng, plies=2, opp_model=named_deck("mega_starmie_ex"), samples=3), deck
    raise ValueError(spec)


def _run_chunk(args):
    """Worker: play `n` games of specA vs specB, return aggregate counts."""
    specA, specB, n, seed = args
    import engine  # noqa: F401
    from engine.harness import play_match

    random.seed(seed)
    a, deck = _build(specA, seed)
    b, _ = _build(specB, seed + 10_000)
    res = play_match(a, b, deck, deck, n_games=n)
    return res["wins_a"], res["wins_b"], res["draws"], res["errors"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games", type=int, default=120, help="games per (matchup, seed)")
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=12, help="games per chunk")
    args = ap.parse_args()

    # (label, specA, specB) — A's win-rate vs B is the reported number.
    matchups = [
        ("1ply        vs heur", "1ply", "heur"),
        ("2ply-gen     vs heur", "2ply-gen", "heur"),
        ("2ply-gen-s3  vs heur", "2ply-gen-s3", "heur"),
        ("2ply-meta-s3 vs heur", "2ply-meta-s3", "heur"),
        ("2ply-gen     vs 1ply", "2ply-gen", "1ply"),
        ("2ply-gen-s3  vs 1ply", "2ply-gen-s3", "1ply"),
    ]

    print(f"=== 2-ply MP battery: {args.games} games x seeds {args.seeds} "
          f"= {args.games * len(args.seeds)} games/matchup, {args.workers} workers ===\n")
    print(f"{'matchup':<24} {'A win%':>7}  {'record':>12}  {'per-seed win%':>22}")
    print("-" * 72)

    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for label, specA, specB in matchups:
            t0 = time.perf_counter()
            seed_rates = []
            tot_a = tot_b = tot_d = tot_e = 0
            for seed in args.seeds:
                # split this (matchup, seed) into chunks
                jobs = []
                remaining = args.games
                k = 0
                while remaining > 0:
                    c = min(args.chunk, remaining)
                    jobs.append((specA, specB, c, seed * 1000 + k))
                    remaining -= c
                    k += 1
                results = list(ex.map(_run_chunk, jobs))
                sa = sum(r[0] for r in results)
                sb = sum(r[1] for r in results)
                sd = sum(r[2] for r in results)
                se = sum(r[3] for r in results)
                tot_a += sa; tot_b += sb; tot_d += sd; tot_e += se
                dec = sa + sb
                seed_rates.append(sa / dec if dec else 0.0)
            dec = tot_a + tot_b
            wr = tot_a / dec if dec else 0.0
            wall = time.perf_counter() - t0
            per_seed = " ".join(f"{r:.0%}" for r in seed_rates)
            print(f"{label:<24} {wr:>6.1%}  {f'{tot_a}-{tot_b} (d{tot_d},e{tot_e})':>12}  "
                  f"{per_seed:>22}   [{wall:.0f}s]")

    print("\nReading: A>50% means A beats B. For the rescue levers (s3 = samples=3,"
          " meta = Mega Starmie opp model) to matter, the 2-ply rows vs heur must"
          " approach/exceed the 1ply-vs-heur row, and the vs-1ply rows must exceed 50%.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
