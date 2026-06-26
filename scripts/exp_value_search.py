"""Measure the value-net-guided search vs the hand-crafted champion.

The deploy base (plies=2, meta opp, samples=1) gets a learned leaf evaluator:
V(state)->P(win) replaces the crude hp-sum board proxy (w_hp=0) and is added as
v_scale*V, kept below W_PRIZE=1000 so an actual prize still dominates. We sweep
v_scale and the V-vs-hp blend vs the heuristic (n=360, 3 seeds), then the best V
config head-to-head vs the hand-crafted baseline.

Run:  python scripts/exp_value_search.py
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

VPATH = "data/checkpoints/value_net.pt"
_V_CACHE = {}


def _get_V():
    # Load the value callable once per worker process.
    if "V" not in _V_CACHE:
        from rl.value_net import load_value_callable
        _V_CACHE["V"] = load_value_callable(VPATH, device="cpu")
    return _V_CACHE["V"]


# config name -> kwargs on the deploy base (plies=2, opp_model, samples=1)
CONFIGS = {
    "baseline":  dict(),                                  # hand-crafted eval (w_hp=1)
    "V300":      dict(w_dmg=0, w_hp=0, v_scale=300),
    "V600":      dict(w_dmg=0, w_hp=0, v_scale=600),
    "V900":      dict(w_dmg=0, w_hp=0, v_scale=900),
    "V600+hp":   dict(w_hp=1, v_scale=600),
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
    cfg = dict(CONFIGS[spec])
    if "v_scale" in cfg:
        cfg["value_net"] = _get_V()
    kw.update(cfg)
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

    print(f"=== Value-net-guided search vs heuristic (n={args.n}x{len(args.seeds)} seeds) ===\n")
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

        # Best V config head-to-head vs the hand-crafted baseline (cleanest test).
        print("\n--- head-to-head vs baseline (is V actually a better player?) ---")
        for spec in ("V600", "V900"):
            t0 = time.perf_counter()
            tot, wr, sr = run_matchup(ex, spec, "baseline", args.seeds, args.n, args.chunk)
            ps = " ".join(f"{r:.0%}" for r in sr)
            print(f"{spec:<12} vs baseline: {wr:>5.1%}  ({tot[0]}-{tot[1]})  {ps}  "
                  f"[{time.perf_counter()-t0:.0f}s]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
