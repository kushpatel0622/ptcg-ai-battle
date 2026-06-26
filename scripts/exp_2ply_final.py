"""Final confirmation for the strengthened SearchTeacher.

Champion config (from the sweeps): 2-ply + Mega Starmie meta opponent model +
samples=3, with the ORIGINAL eval (the re-baseline "fix" was measured worse and
reverted). This script:
  1. confirms the champion reproduces ~73% vs the heuristic after the revert,
  2. runs the missing HEAD-TO-HEAD vs the strong 1-ply agent (the real skill test),
  3. checks that the per-move time-budget guard (time_budget=0.8s) caps tail
     latency without cratering win-rate.

Parallelised across cores; each worker has its own cg.dll.

Run:  python scripts/exp_2ply_final.py
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
    table = {
        "1ply": dict(plies=1),
        "2ply-meta-s3": dict(plies=2, opp_model=starmie, samples=3),
        "2ply-meta-s3-tb": dict(plies=2, opp_model=starmie, samples=3, time_budget=0.8),
    }
    return SearchTeacher(deck=deck, rng=rng, **table[spec]), deck


def _run_chunk(args):
    specA, specB, n, seed = args
    import engine  # noqa: F401
    from engine.harness import play_match

    random.seed(seed)
    a_raw, deck = _build(specA, seed)
    a = Timed(a_raw)
    b, _ = _build(specB, seed + 10_000)
    res = play_match(a, b, deck, deck, n_games=n)
    return (res["wins_a"], res["wins_b"], res["draws"], res["errors"],
            a.total, a.calls, a.max)


def run_matchup(ex, specA, specB, seeds, n, chunk):
    tot = [0, 0, 0, 0]
    ttime, tcalls, tmax = 0.0, 0, 0.0
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
        ttime += sum(r[4] for r in results); tcalls += sum(r[5] for r in results)
        tmax = max(tmax, max(r[6] for r in results))
        seed_rates.append(sa / (sa + sb) if (sa + sb) else 0.0)
    dec = tot[0] + tot[1]
    return tot, (tot[0] / dec if dec else 0.0), seed_rates, \
        (1000.0 * ttime / tcalls if tcalls else 0.0), 1000.0 * tmax


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=12)
    args = ap.parse_args()

    jobs = [
        ("2ply-meta-s3      vs heur", "2ply-meta-s3", "heur", [1, 2, 3], 120),
        ("2ply-meta-s3      vs 1ply", "2ply-meta-s3", "1ply", [1, 2, 3], 120),
        ("2ply-meta-s3-tb   vs heur", "2ply-meta-s3-tb", "heur", [1, 2], 120),
    ]

    print("=== FINAL confirmation: champion = 2-ply + meta opp + samples=3 (orig eval) ===\n")
    print(f"{'matchup':<28} {'A win%':>7}  {'record':>13}  {'per-seed':>11}  {'ms/mv':>6} {'max':>6}  time")
    print("-" * 90)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for label, specA, specB, seeds, n in jobs:
            t0 = time.perf_counter()
            tot, wr, sr, avg_ms, max_ms = run_matchup(ex, specA, specB, seeds, n, args.chunk)
            wall = time.perf_counter() - t0
            ps = " ".join(f"{r:.0%}" for r in sr)
            print(f"{label:<28} {wr:>6.1%}  {f'{tot[0]}-{tot[1]} (e{tot[3]})':>13}  "
                  f"{ps:>11}  {avg_ms:>5.0f} {max_ms:>5.0f}  [{wall:.0f}s]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
