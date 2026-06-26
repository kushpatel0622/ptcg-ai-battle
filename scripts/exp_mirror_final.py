"""Deep head-to-head to pick the single best submission deck:
mega_starmie_ex_2 (2-ply) vs mega_starmie_ex (at both 1-ply and 2-ply).
Large n, all cores, hang-proofed (max_steps + chunk timeout), Wilson lb95.

Run:  python scripts/exp_mirror_final.py
"""
from __future__ import annotations
import math, os, random, sys, time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# (label, A_deck, A_plies, B_deck, B_plies) — report A's win% vs B
MATCHUPS = [
    ("msx2(2ply) vs msx(1ply)", "mega_starmie_ex_2", 2, "mega_starmie_ex", 1),
    ("msx2(2ply) vs msx(2ply)", "mega_starmie_ex_2", 2, "mega_starmie_ex", 2),
    ("msx2(1ply) vs msx(1ply)", "mega_starmie_ex_2", 1, "mega_starmie_ex", 1),
]


def _chunk(args):
    aD, aP, bD, bP, n, seed = args
    import engine  # noqa: F401
    from engine.decks import named_deck
    from engine.harness import play_match
    from rl.search_teacher import SearchTeacher
    random.seed(seed)
    dA, dB = named_deck(aD), named_deck(bD)
    a = SearchTeacher(deck=dA, rng=random.Random(seed), plies=aP, samples=1, dynamic_attack=True)
    b = SearchTeacher(deck=dB, rng=random.Random(seed + 7), plies=bP, samples=1, dynamic_attack=True)
    res = play_match(a, b, dA, dB, n_games=n, max_steps=4000)
    return res["wins_a"], res["wins_b"]


def _lb(w, d, z=1.645):
    if not d: return 0.0
    p = w / d
    return (p + z*z/(2*d) - z*math.sqrt(p*(1-p)/d + z*z/(4*d*d))) / (1 + z*z/d)


def main():
    seeds = list(range(1, 10))   # 9 seeds
    n = 200                       # 1800 games/matchup
    print(f"=== Deep mirror head-to-head (n={n}x{len(seeds)}={n*len(seeds)}/matchup) ===\n")
    print(f"{'matchup':<26} {'A win%':>7} {'lb95':>6}  {'record':>13}  per-seed")
    print("-" * 80)
    with ProcessPoolExecutor(max_workers=12) as ex:
        for label, aD, aP, bD, bP in MATCHUPS:
            wa = wb = 0; srates = []
            t0 = time.perf_counter()
            for seed in seeds:
                jobs, rem, k = [], n, 0
                while rem > 0:
                    c = min(12, rem); jobs.append((aD, aP, bD, bP, c, seed*1000+k)); rem -= c; k += 1
                swa = swb = 0
                for f in [ex.submit(_chunk, j) for j in jobs]:
                    try:
                        r = f.result(timeout=480); swa += r[0]; swb += r[1]
                    except Exception:
                        pass
                wa += swa; wb += swb
                srates.append(swa/(swa+swb) if (swa+swb) else 0)
            d = wa + wb
            ps = " ".join(f"{r:.0%}" for r in srates)
            print(f"{label:<26} {(wa/d if d else 0):>6.1%} {_lb(wa,d):>5.1%}  {f'{wa}-{wb}':>13}  {ps}  [{time.perf_counter()-t0:.0f}s]")
    print("\nA = mega_starmie_ex_2. A>50% => mega_starmie_ex_2 is the #1 submission deck.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
