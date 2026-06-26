"""Non-mirror robustness check for the strengthened SearchTeacher.

Every prior benchmark was the dual_mega_water MIRROR, and the meta-opponent model
(mega_starmie_ex) is itself a Water deck — so it roughly matches the mirror
opponent, which may flatter the "meta opponent" lever. The real ladder is diverse
and our opponent model will usually be WRONG about the opponent's deck.

This battery keeps OUR deck = dual_mega_water (and our opp_model = mega_starmie_ex)
but has the heuristic opponent pilot a DIFFERENT, non-Water archetype, so the meta
model is deliberately mismatched. If 2ply-meta-s1 keeps its edge over 1ply here,
the strengthening generalizes; if it collapses to ~1ply, the mirror flattered it.

Run:  python scripts/exp_2ply_robust.py
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _build_agent(spec, seed):
    import engine  # noqa: F401
    from baselines.heuristic_agent import heuristic_agent
    from engine.decks import named_deck
    from rl.search_teacher import SearchTeacher

    our_deck = named_deck("dual_mega_water")
    if spec == "heur":
        return heuristic_agent
    rng = random.Random(seed)
    starmie = named_deck("mega_starmie_ex")
    table = {
        "1ply": dict(plies=1),
        "2ply-meta-s1": dict(plies=2, opp_model=starmie, samples=1),
    }
    return SearchTeacher(deck=our_deck, rng=rng, **table[spec])


def _run_chunk(args):
    specA, opp_deck_name, n, seed = args
    import engine  # noqa: F401
    from engine.decks import named_deck
    from engine.harness import play_match

    random.seed(seed)
    a = _build_agent(specA, seed)
    b = _build_agent("heur", seed)
    our_deck = named_deck("dual_mega_water")
    opp_deck = named_deck(opp_deck_name)
    # A pilots our deck; B (heuristic) pilots the opponent archetype.
    res = play_match(a, b, our_deck, opp_deck, n_games=n)
    return res["wins_a"], res["wins_b"], res["draws"], res["errors"]


def run_matchup(ex, specA, opp_deck, seeds, n, chunk):
    tot = [0, 0, 0, 0]
    seed_rates = []
    for seed in seeds:
        jobs, remaining, k = [], n, 0
        while remaining > 0:
            c = min(chunk, remaining)
            jobs.append((specA, opp_deck, c, seed * 1000 + k))
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
    args = ap.parse_args()

    # (label, specA, opp_deck_name, seeds, n) — A always pilots dual_mega_water.
    jobs = [
        ("1ply         vs heur[charizard_fire]", "1ply", "charizard_fire", [1, 2, 3], 120),
        ("2ply-meta-s1 vs heur[charizard_fire]", "2ply-meta-s1", "charizard_fire", [1, 2, 3], 120),
        ("1ply         vs heur[lightning_counter]", "1ply", "lightning_counter", [1, 2], 120),
        ("2ply-meta-s1 vs heur[lightning_counter]", "2ply-meta-s1", "lightning_counter", [1, 2], 120),
        ("1ply         vs heur[gardevoir_psychic]", "1ply", "gardevoir_psychic", [1, 2], 120),
        ("2ply-meta-s1 vs heur[gardevoir_psychic]", "2ply-meta-s1", "gardevoir_psychic", [1, 2], 120),
    ]

    print("=== NON-MIRROR robustness: our deck=dual_mega_water vs diverse opponents ===")
    print("  (our opp_model=mega_starmie_ex is deliberately mismatched to the opponent)\n")
    print(f"{'matchup':<42} {'win%':>6}  {'record':>13}  {'per-seed':>11}  time")
    print("-" * 86)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for label, specA, opp, seeds, n in jobs:
            t0 = time.perf_counter()
            tot, wr, sr = run_matchup(ex, specA, opp, seeds, n, args.chunk)
            wall = time.perf_counter() - t0
            ps = " ".join(f"{r:.0%}" for r in sr)
            print(f"{label:<42} {wr:>5.1%}  {f'{tot[0]}-{tot[1]} (e{tot[3]})':>13}  "
                  f"{ps:>11}  [{wall:.0f}s]")
    print("\nVerdict: compare each 2ply-meta-s1 row to the 1ply row vs the SAME opponent.")
    print("If 2ply-meta-s1 stays clearly above 1ply, the strengthening generalizes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
