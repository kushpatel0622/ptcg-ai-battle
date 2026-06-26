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
    ("mega_starmie_ex", 2),       # peer Water aggro (the replay killer line)
    ("starmie_aggro_tuned", 2),   # Water aggro variant
    ("lightning_counter", 2),     # Lightning
    ("dragapult_ex_meta", 2),     # Dragon/spread
]
BASE_CFG = dict(plies=2, samples=1, dynamic_attack=True)

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


PEER = GAUNTLET[0][0]   # the discriminating matchup (closest proxy to strong ladder decks)


def evaluate(ex, deck, cfg, n_per_opp, base_seed, chunk=15, timeout=1200):
    """Peer-primary fitness. The PEER (the only close, discriminating matchup) gets
    2x games for a tighter CI and is the OBJECTIVE; the other 3 decks form a FIELD
    no-regression guard (we already win them ~80-97%, so trading peer% for field% is
    over-fitting). Returns peer_wr (+lb95) and field_wr separately."""
    per_opp = {}
    tot_err = 0
    for name, opp_plies in GAUNTLET:
        n = n_per_opp * (2 if name == PEER else 1)
        jobs, rem, k = [], n, 0
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
    pw, pdec, pwr = per_opp[PEER]
    fw = sum(per_opp[k][0] for k in per_opp if k != PEER)
    fdec = sum(per_opp[k][1] for k in per_opp if k != PEER)
    aw = pw + fw; adec = pdec + fdec
    return dict(peer_wr=pwr, peer_w=pw, peer_dec=pdec, peer_lb95=wilson_lb95(pw, pdec),
                field_wr=(fw / fdec if fdec else 0.0), field_w=fw, field_dec=fdec,
                wr=(aw / adec if adec else 0.0), dec=adec, per_opp=per_opp, err=tot_err)


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
                f"PEER {champ_res['peer_wr']:.1%} (lb95 {champ_res['peer_lb95']:.1%}, "
                f"n={champ_res['peer_dec']})  field {champ_res['field_wr']:.1%}  "
                f"agg {champ_res['wr']:.1%}")
            best = None
            for label, deck, cfg in challengers:
                if not _legal(deck):
                    log(f"  - {label}: ILLEGAL, skipped"); continue
                r = evaluate(ex, deck, cfg, args.n_per_opp, seed)
                rec = dict(round=rnd, ts=_ts(), label=label, peer_wr=r["peer_wr"],
                           peer_lb95=r["peer_lb95"], field_wr=r["field_wr"], wr=r["wr"],
                           n=r["dec"], per_opp={k: v[2] for k, v in r["per_opp"].items()},
                           config=cfg)
                hist(rec)
                po = " ".join(f"{k.split('_')[0]}:{v[2]:.0%}" for k, v in r["per_opp"].items())
                # PEER-PRIMARY promotion: must improve the hard matchup with lb95
                # confidence AND not regress the field (>3pt). Prevents trading the
                # discriminating peer% for already-won easy decks (over-fit).
                beats = (r["peer_wr"] > champ_res["peer_wr"] + args.promote_margin
                         and r["peer_lb95"] >= champ_res["peer_wr"]
                         and r["field_wr"] >= champ_res["field_wr"] - 0.03)
                tag = "  <== beats champion (peer)" if beats else ""
                if beats and (best is None or r["peer_wr"] > best[1]["peer_wr"]):
                    best = (label, r, deck, cfg)
                log(f"  - {label}: PEER {r['peer_wr']:.1%} (lb95 {r['peer_lb95']:.1%}) "
                    f"field {r['field_wr']:.1%} [{po}]{tag}")

            def _champ_record(lbl, dck, cf, res):
                return dict(label=lbl, deck=dck, config=cf, score=res["peer_wr"],
                            peer_wr=res["peer_wr"], field_wr=res["field_wr"],
                            per_opp={k: v[2] for k, v in res["per_opp"].items()},
                            n=res["dec"], ts=_ts())

            if best is not None:
                label, r, deck, cfg = best
                champ = _champ_record(label, deck, cfg, r)
                save_champion(champ)
                log(f"  >> PROMOTED new champion: {label}  PEER {r['peer_wr']:.1%} "
                    f"(lb95 {r['peer_lb95']:.1%})  field {r['field_wr']:.1%}")
            else:
                champ = _champ_record(champ["label"], champ["deck"], champ["config"], champ_res)
                save_champion(champ)
        log(f"\n## opt_loop stop {datetime.now():%H:%M:%S}  rounds={rnd}  "
            f"champion='{champ['label']}' score={champ.get('score')}")


if __name__ == "__main__":
    raise SystemExit(main())
