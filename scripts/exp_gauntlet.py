"""Non-mirror evaluation gauntlet (the honest eval; supersedes mirror tournaments).

Our deck, piloted by a chosen SearchTeacher CONFIG, plays a fixed, DIVERSE,
well-piloted opponent set (Water/Fire/Psychic/Lightning/Dragon/control), BOTH
seats, multi-seed. Reports per-opponent win% and an aggregate with a Wilson
lower-95% bound (treat sub-~5pt gaps as noise; the engine RNG is unseeded).

Every agent variant is compared against the SAME gauntlet, so deltas are real.

Run:
  python scripts/exp_gauntlet.py --config baseline -n 60
  python scripts/exp_gauntlet.py --config develop  -n 60        # compare a variant
  python scripts/exp_gauntlet.py --list                         # show configs
Hang-proofed: play_match(max_steps=4000) + per-chunk future timeout.
"""
from __future__ import annotations
import argparse, math, os, random, sys, time
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FTimeout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUR_DECK_DEFAULT = "mega_starmie_ex_2"

# Diverse, well-piloted opponents (name -> archetype tag). mega_starmie_ex is the
# strong near-peer (the tournament #1) and the key discriminator; the rest probe
# matchup robustness across types so we don't over-fit one matchup.
GAUNTLET = [
    ("mega_starmie_ex",      "Water-aggro(peer)"),
    ("charizard_fire",       "Fire"),
    ("gardevoir_psychic",    "Psychic"),
    ("lightning_counter",    "Lightning"),
    ("dragapult_spread",     "Dragon/spread"),
    ("single_prize_control", "Control"),
]

# OUR-agent variants. Each maps to SearchTeacher kwargs (deck/rng added per worker).
# opp_model is given as a DECK NAME (resolved in the worker) to stay picklable.
_BASE = dict(plies=2, samples=1, dynamic_attack=True)
CONFIGS = {
    "baseline":  dict(_BASE),
    "1ply":      dict(plies=1, samples=1, dynamic_attack=True),
    # Phase 1: improved rollout pilot (lethal-KO; bench-when-thin variant separate).
    "improved":  dict(_BASE, rollout_policy="improved"),
    "improved_bench": dict(_BASE, rollout_policy="improved_bench"),
    # Phase 2: config/eval tuning ON TOP of the improved pilot.
    "imp_m5":    dict(_BASE, rollout_policy="improved", override_margin=5.0),
    "imp_m50":   dict(_BASE, rollout_policy="improved", override_margin=50.0),
    "imp_m100":  dict(_BASE, rollout_policy="improved", override_margin=100.0),
    "imp_wdmg5": dict(_BASE, rollout_policy="improved", w_dmg=5.0),
    "imp_wdmg10":dict(_BASE, rollout_policy="improved", w_dmg=10.0),
    "imp_whp2":  dict(_BASE, rollout_policy="improved", w_hp=2.0),
    "imp_s3":    dict(_BASE, rollout_policy="improved", samples=3),
    "oppmodel":  dict(_BASE, opp_model_name="mega_starmie_ex"),
    # S1: develop a bench / avoid being one KO from a board-out.
    "develop":   dict(_BASE, w_bench=60.0, fragile_penalty=600.0, bench_target=3),
    # S2: hand discipline vs Resentful Refrain (needs a model that can field it).
    "discipline": dict(_BASE, opp_model_name="mega_starmie_ex", w_handpen=40.0),
    # S1+S2 combined.
    "robust":    dict(_BASE, opp_model_name="mega_starmie_ex",
                      w_bench=60.0, fragile_penalty=600.0, bench_target=3, w_handpen=40.0),
    # S3: spend the time budget — deeper rollout horizon, on top of develop terms.
    "develop3":  dict(plies=3, samples=1, dynamic_attack=True,
                      w_bench=60.0, fragile_penalty=600.0, bench_target=3),
    "robust3":   dict(plies=3, samples=1, dynamic_attack=True, opp_model_name="mega_starmie_ex",
                      w_bench=60.0, fragile_penalty=600.0, bench_target=3, w_handpen=40.0),
    # S1 magnitude sweep (around the develop winner) to find the best calibration.
    "dev_f1000": dict(_BASE, w_bench=60.0, fragile_penalty=1000.0, bench_target=3),
    "dev_f1500": dict(_BASE, w_bench=60.0, fragile_penalty=1500.0, bench_target=3),
    "dev_b120":  dict(_BASE, w_bench=120.0, fragile_penalty=600.0, bench_target=3),
    "dev_bt2":   dict(_BASE, w_bench=60.0, fragile_penalty=600.0, bench_target=2),
}


def wilson_lb95(wins: int, n: int) -> float:
    if n == 0:
        return 0.0
    z = 1.96
    p = wins / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (c - m) / d


def _build_agent(cfg: dict, deck, seed):
    from rl.search_teacher import SearchTeacher
    from engine.decks import named_deck
    kw = dict(cfg)
    om = kw.pop("opp_model_name", None)
    if om:
        kw["opp_model"] = named_deck(om)
    return SearchTeacher(deck=deck, rng=random.Random(seed), **kw)


def _run_chunk(args):
    our_deck_name, opp_name, our_cfg, opp_cfg, n, seed = args
    import engine  # noqa: F401  (puts submission/ on path so `cg` imports)
    from engine.decks import named_deck
    from engine.harness import play_match
    random.seed(seed)
    our = named_deck(our_deck_name)
    opp = named_deck(opp_name)
    a = _build_agent(our_cfg, our, seed)
    b = _build_agent(opp_cfg, opp, seed + 10_000)
    res = play_match(a, b, our, opp, n_games=n, max_steps=4000)
    return res["wins_a"], res["wins_b"], res["draws"], res["errors"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="baseline", help="our-agent variant (see --list)")
    ap.add_argument("--our-deck", default=OUR_DECK_DEFAULT)
    ap.add_argument("--opp-plies", type=int, default=1, help="opponent search depth (1=fast,2=strong)")
    ap.add_argument("-n", type=int, default=60, help="games per opponent (both seats)")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=10)
    ap.add_argument("--timeout", type=int, default=900, help="per-chunk wall timeout (s)")
    ap.add_argument("--only", default=None, help="comma-sep opponent names to restrict to")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        print("CONFIGS:")
        for k, v in CONFIGS.items():
            print(f"  {k:10} {v}")
        print("\nGAUNTLET:", [n for n, _ in GAUNTLET])
        return 0

    if args.config not in CONFIGS:
        sys.exit(f"unknown config '{args.config}'. Options: {list(CONFIGS)}")
    our_cfg = CONFIGS[args.config]
    opp_cfg = dict(plies=args.opp_plies, samples=1, dynamic_attack=True)

    print(f"=== GAUNTLET: our={args.our_deck} cfg='{args.config}' {our_cfg}")
    print(f"    opponents piloted at plies={args.opp_plies}, n={args.n}/opp, both seats\n")
    print(f"{'opponent':<22} {'type':<18} {'win%':>6} {'lb95':>6} {'record':>14} {'time':>7}")
    print("-" * 78)

    gauntlet = GAUNTLET
    if args.only:
        keep = set(args.only.split(","))
        gauntlet = [(n, t) for n, t in GAUNTLET if n in keep]

    tot_w = tot_dec = tot_err = 0
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for name, tag in gauntlet:
            t0 = time.perf_counter()
            jobs, rem, k = [], args.n, 0
            while rem > 0:
                c = min(args.chunk, rem)
                jobs.append((args.our_deck, name, our_cfg, opp_cfg, c, 2000 + k))
                rem -= c; k += 1
            futs = [ex.submit(_run_chunk, j) for j in jobs]
            w = l = dr = er = 0
            for f in futs:
                try:
                    a, b, d, e = f.result(timeout=args.timeout)
                    w += a; l += b; dr += d; er += e
                except FTimeout:
                    er += 1
                    print(f"  ! chunk timeout on {name}")
            dec = w + l
            wr = w / dec if dec else 0.0
            lb = wilson_lb95(w, dec)
            wall = time.perf_counter() - t0
            rows.append((name, tag, wr, lb, w, l, er))
            tot_w += w; tot_dec += dec; tot_err += er
            print(f"{name:<22} {tag:<18} {wr:>5.1%} {lb:>5.1%} {f'{w}-{l} (e{er})':>14} {wall:>6.0f}s")

    print("-" * 78)
    agg_wr = tot_w / tot_dec if tot_dec else 0.0
    agg_lb = wilson_lb95(tot_w, tot_dec)
    print(f"{'AGGREGATE':<22} {'':<18} {agg_wr:>5.1%} {agg_lb:>5.1%} "
          f"{f'{tot_w}-{tot_dec - tot_w} (e{tot_err})':>14}")
    print(f"\nconfig='{args.config}'  aggregate win {agg_wr:.1%} (lb95 {agg_lb:.1%}) over n={tot_dec} decisive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
