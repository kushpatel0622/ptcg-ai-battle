"""Autonomous deck+config optimizer (runs for hours, uses all cores).

Maintains a CHAMPION (deck + SearchTeacher config) and relentlessly tests
CHALLENGERS against a fixed, diverse, STRONGLY-PILOTED gauntlet at HIGH n
(the only trustworthy sample size — see docs/REPORT.md §3.1). A challenger is
promoted only if it beats the champion *this round* with a Wilson lb95 guard
(conservative — avoids promoting on unseeded-RNG noise).

Challenger sources, in order:
  1. data/opt/queue.jsonl  — externally proposed (LLM analysts, curated edits);
     each line: {"label":..., "deck_name":... | "deck":[60 ints], "config":{...}}.
  2. systematic single-card swaps mutated from the current champion deck.
Champion always re-evaluated each round (fresh games) for a fair comparison.

State (all under data/opt/):
  champion.json   — current best {label, deck, config, score, per_opp, n, ts}
  log.md          — append-only, timestamped round log (the audit trail)
  queue.jsonl     — challenger inbox (consumed)
  history.jsonl   — every evaluated challenger's result

Run (background):
  python scripts/opt_loop.py --until 16:25 --n-per-opp 150 --batch 5 --workers 11
"""
from __future__ import annotations
import argparse, json, math, os, random, sys, time
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FTimeout
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
OPT = os.path.join(REPO, "data", "opt")
os.makedirs(OPT, exist_ok=True)
CHAMP = os.path.join(OPT, "champion.json")
QUEUE = os.path.join(OPT, "queue.jsonl")
LOG = os.path.join(OPT, "log.md")
HIST = os.path.join(OPT, "history.jsonl")

# Strong, DIVERSE gauntlet (anti-over-fit): (deck_name, opp_plies). Piloted at
# plies=2 so they are well-played (the "smart tests"). Spread of archetypes.
GAUNTLET = [
    ("opp_lucario", 2),           # REAL ladder counter (Fighting, Mega Lucario ex) — 3/4 losses
    ("opp_bellibolt", 2),         # REAL ladder counter (Lightning, Iono/Bellibolt ex) — 1/4 losses
    ("mega_starmie_ex", 2),       # the mirror peer (no-regression guard)
    ("dragapult_ex_meta", 2),     # a field deck (no-regression guard)
]
# Fitness = win% vs the decks that ACTUALLY beat us; the rest are no-regression guards.
PRIMARY = {"opp_lucario", "opp_bellibolt"}
# Champion ships the improved (lethal-KO) rollout pilot proven in S7/S7b.
BASE_CFG = dict(plies=2, samples=1, dynamic_attack=True, rollout_policy="improved")

# Systematic swap pool (fallback when the queue is empty). Cuts target flex
# slots; adds are Water-deck-sensible consistency/utility cards.
FLEX_CUTS = [1119, 1122, 1225, 1211, 1229, 1145, 1252]          # energy search, pokegear, hilda, black belt, wally's, mega signal, gravity mtn
ADDS = [1121, 1132, 1097, 3, 1182, 1123, 1086, 1189, 1227]       # ultra ball, great ball, night stretcher, water, boss's, switch, poffin, salvatore, lillie's


def wilson_lb95(w, n):
    if n == 0:
        return 0.0
    z = 1.96; p = w / n
    return (p + z*z/(2*n) - z*math.sqrt((p*(1-p)+z*z/(4*n))/n)) / (1 + z*z/n)


def _ts():
    return datetime.now().strftime("%H:%M:%S")


def _legal(deck):
    """60 cards, <=4 of any non-basic-energy card, and starts a battle."""
    if len(deck) != 60:
        return False
    from collections import Counter
    for cid, k in Counter(deck).items():
        if cid > 100 and k > 4:
            return False
    try:
        import engine  # noqa
        from cg.game import battle_start, battle_finish
        obs, start = battle_start(deck, deck)
        ok = obs is not None
        if ok:
            battle_finish()
        return ok
    except Exception:
        return False


def _chunk(args):
    our_deck, opp_name, our_cfg, opp_plies, n, seed = args
    import engine  # noqa
    from engine.decks import named_deck
    from engine.harness import play_match
    from scripts.exp_gauntlet import _build_agent
    random.seed(seed)
    opp = named_deck(opp_name)
    a = _build_agent(our_cfg, our_deck, seed)
    b = _build_agent(dict(plies=opp_plies, samples=1, dynamic_attack=True), opp, seed + 99999)
    res = play_match(a, b, our_deck, opp, n_games=n, max_steps=4000)
    return res["wins_a"], res["wins_b"], res["draws"], res["errors"]


def evaluate(ex, deck, cfg, n_per_opp, base_seed, chunk=15, timeout=1200):
    """PRIMARY-primary fitness. Win% vs the PRIMARY decks (the real counters that beat
    us) is the OBJECTIVE; the remaining GUARD decks (mirror + a field deck) must not
    regress. Returns prim_wr (+lb95) and guard_wr separately so we improve vs what
    beats us without breaking the matchups we already win."""
    per_opp = {}
    tot_err = 0
    for name, opp_plies in GAUNTLET:
        jobs, rem, k = [], n_per_opp, 0
        while rem > 0:
            c = min(chunk, rem)
            jobs.append((deck, name, cfg, opp_plies, c, base_seed + k * 131 + hash(name) % 1000))
            rem -= c; k += 1
        w = l = er = 0
        for f in [ex.submit(_chunk, j) for j in jobs]:
            try:
                a, b, d, e = f.result(timeout=timeout)
                w += a; l += b; er += e
            except FTimeout:
                er += 1
        per_opp[name] = (w, w + l, (w / (w + l) if (w + l) else 0.0))
        tot_err += er
    pw = sum(per_opp[k][0] for k in per_opp if k in PRIMARY)
    pdec = sum(per_opp[k][1] for k in per_opp if k in PRIMARY)
    gw = sum(per_opp[k][0] for k in per_opp if k not in PRIMARY)
    gdec = sum(per_opp[k][1] for k in per_opp if k not in PRIMARY)
    return dict(prim_wr=(pw / pdec if pdec else 0.0), prim_w=pw, prim_dec=pdec,
                prim_lb95=wilson_lb95(pw, pdec),
                guard_wr=(gw / gdec if gdec else 1.0), guard_w=gw, guard_dec=gdec,
                wr=((pw + gw) / (pdec + gdec) if (pdec + gdec) else 0.0),
                dec=pdec + gdec, per_opp=per_opp, err=tot_err)


def load_champion():
    if os.path.exists(CHAMP):
        with open(CHAMP) as f:
            return json.load(f)
    from engine.decks import named_deck
    return dict(label="baseline:mega_starmie_ex_2",
                deck=named_deck("mega_starmie_ex_2"), config=dict(BASE_CFG),
                score=None, per_opp=None, n=0, ts=_ts())


def save_champion(ch):
    tmp = CHAMP + ".tmp"
    with open(tmp, "w") as f:
        json.dump(ch, f)
    os.replace(tmp, CHAMP)


def log(line):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def hist(rec):
    with open(HIST, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def read_queue(maxn):
    """Consume up to maxn challengers from the queue file (atomic-ish)."""
    if not os.path.exists(QUEUE):
        return []
    with open(QUEUE, encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    take, rest = lines[:maxn], lines[maxn:]
    with open(QUEUE, "w", encoding="utf-8") as f:
        f.write("\n".join(rest) + ("\n" if rest else ""))
    out = []
    from engine.decks import named_deck
    for ln in take:
        try:
            spec = json.loads(ln)
            deck = spec.get("deck") or named_deck(spec["deck_name"])
            cfg = dict(BASE_CFG); cfg.update(spec.get("config") or {})
            out.append((spec.get("label", "queued"), list(deck), cfg))
        except Exception as e:
            log(f"  [queue parse error] {e}")
    return out


def gen_swaps(champion_deck, k, rng):
    """k random legal single-card swaps mutated from the champion deck."""
    from collections import Counter
    out = []
    tries = 0
    while len(out) < k and tries < k * 8:
        tries += 1
        deck = list(champion_deck)
        cut = rng.choice([c for c in FLEX_CUTS if c in deck] or FLEX_CUTS)
        add = rng.choice(ADDS)
        if cut not in deck:
            continue
        if Counter(deck).get(add, 0) >= 4 and add > 100:
            continue
        deck.remove(cut); deck.append(add)
        if _legal(deck):
            out.append((f"swap -{cut}+{add}", deck, dict(BASE_CFG)))
    return out


def parse_until(s):
    if s.isdigit():
        return float(s)
    hh, mm = s.split(":")
    now = datetime.now()
    tgt = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    return tgt.timestamp()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--until", default="16:25", help="stop time HH:MM (local) or epoch")
    ap.add_argument("--n-per-opp", type=int, default=150)
    ap.add_argument("--batch", type=int, default=5)
    ap.add_argument("--workers", type=int, default=11)
    ap.add_argument("--promote-margin", type=float, default=0.0,
                    help="extra pts challenger point-est must exceed champion (lb95 guard always applies)")
    args = ap.parse_args()
    until = parse_until(args.until)

    import engine  # noqa
    champ = load_champion()
    log(f"\n## opt_loop start {datetime.now():%Y-%m-%d %H:%M:%S}  until={args.until}  "
        f"n/opp={args.n_per_opp} batch={args.batch} gauntlet={[g[0] for g in GAUNTLET]}")
    log(f"champion: {champ['label']}")
    rng = random.Random(12345)
    rnd = 0
    seed = 50000
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        while time.time() < until:
            rnd += 1
            challengers = read_queue(args.batch)
            src = "queue"
            if not challengers:
                challengers = gen_swaps(champ["deck"], args.batch, rng)
                src = "swaps"
            if not challengers:
                log(f"[round {rnd} {_ts()}] no challengers; sleeping"); time.sleep(30); continue

            seed += 1000
            champ_res = evaluate(ex, champ["deck"], champ["config"], args.n_per_opp, seed)
            log(f"\n[round {rnd} {_ts()}] src={src}  champ '{champ['label']}'  "
                f"PRIMARY(counters) {champ_res['prim_wr']:.1%} (lb95 {champ_res['prim_lb95']:.1%}, "
                f"n={champ_res['prim_dec']})  guard {champ_res['guard_wr']:.1%}  "
                f"[{' '.join(f'{k.split(chr(95))[0]}:{v[2]:.0%}' for k,v in champ_res['per_opp'].items())}]")
            best = None
            for label, deck, cfg in challengers:
                if not _legal(deck):
                    log(f"  - {label}: ILLEGAL, skipped"); continue
                r = evaluate(ex, deck, cfg, args.n_per_opp, seed)
                rec = dict(round=rnd, ts=_ts(), label=label, prim_wr=r["prim_wr"],
                           prim_lb95=r["prim_lb95"], guard_wr=r["guard_wr"], wr=r["wr"],
                           n=r["dec"], per_opp={k: v[2] for k, v in r["per_opp"].items()},
                           config=cfg)
                hist(rec)
                po = " ".join(f"{k.split('_')[0]}:{v[2]:.0%}" for k, v in r["per_opp"].items())
                # PRIMARY-primary promotion: must improve win% vs the real counters with
                # lb95 confidence AND not regress the guard (mirror/field) by >4pt.
                beats = (r["prim_wr"] > champ_res["prim_wr"] + args.promote_margin
                         and r["prim_lb95"] >= champ_res["prim_wr"]
                         and r["guard_wr"] >= champ_res["guard_wr"] - 0.04)
                tag = "  <== beats champion (counters)" if beats else ""
                if beats and (best is None or r["prim_wr"] > best[1]["prim_wr"]):
                    best = (label, r, deck, cfg)
                log(f"  - {label}: counters {r['prim_wr']:.1%} (lb95 {r['prim_lb95']:.1%}) "
                    f"guard {r['guard_wr']:.1%} [{po}]{tag}")

            def _champ_record(lbl, dck, cf, res):
                return dict(label=lbl, deck=dck, config=cf, score=res["prim_wr"],
                            prim_wr=res["prim_wr"], guard_wr=res["guard_wr"],
                            per_opp={k: v[2] for k, v in res["per_opp"].items()},
                            n=res["dec"], ts=_ts())

            if best is not None:
                label, r, deck, cfg = best
                champ = _champ_record(label, deck, cfg, r)
                save_champion(champ)
                log(f"  >> PROMOTED new champion: {label}  counters {r['prim_wr']:.1%} "
                    f"(lb95 {r['prim_lb95']:.1%})  guard {r['guard_wr']:.1%}")
            else:
                champ = _champ_record(champ["label"], champ["deck"], champ["config"], champ_res)
                save_champion(champ)
        log(f"\n## opt_loop stop {datetime.now():%H:%M:%S}  rounds={rnd}  "
            f"champion='{champ['label']}' score={champ.get('score')}")


if __name__ == "__main__":
    raise SystemExit(main())
