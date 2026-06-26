"""Run the 8-deck tournament in 4 rounds of 7 pairs each, so each round's
completion re-pings the caller for a progress report. Accumulates results in
data/tourney_acc.txt; builds tournaments/8_deck_tourney.md after round 4.
Hang-proofed (max_steps cap + per-chunk timeout).

Run:  python scripts/exp_tourney_batch.py <round 0..3>
"""
from __future__ import annotations
import itertools, os, sys, time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp_tournament as T

ACC = "data/tourney_acc.txt"
N = 200
BATCH = 7


def _chunk(args):
    dA, dB, n, seed = args
    import random, engine  # noqa: F401
    from engine.harness import play_match
    random.seed(seed)
    a, deckA = T._build(dA, seed)
    b, deckB = T._build(dB, seed + 10_000)
    res = play_match(a, b, deckA, deckB, n_games=n, max_steps=4000)
    return res["wins_a"], res["wins_b"]


def run_pair(ex, dA, dB):
    jobs, rem, k = [], N, 0
    while rem > 0:
        c = min(12, rem); jobs.append((dA, dB, c, 100 + k)); rem -= c; k += 1
    wa = wb = 0
    for f in [ex.submit(_chunk, j) for j in jobs]:
        try:
            r = f.result(timeout=480); wa += r[0]; wb += r[1]
        except Exception:
            pass
    return wa, wb


def build_report(decks):
    win = {a: {b: 0 for b in decks} for a in decks}
    dec = {a: {b: 0 for b in decks} for a in decks}
    for line in open(ACC):
        dA, dB, wa, wb = line.split()
        wa, wb = int(wa), int(wb)
        win[dA][dB] += wa; win[dB][dA] += wb
        dec[dA][dB] += wa + wb; dec[dB][dA] += wa + wb
    rank = []
    for a in decks:
        tw = sum(win[a][b] for b in decks if b != a); td = sum(dec[a][b] for b in decks if b != a)
        rank.append((a, tw / td if td else 0.0, tw, td))
    rank.sort(key=lambda r: -r[1])
    short = {d: d.replace("_", " ")[:13] for d in decks}
    L = ["# 8-Deck Round-Robin Tournament (re-run, aggressive combo configs)\n",
         f"_{N} games/pair, 8 decks, 28 matchups. Combo decks now piloted with `w_dmg=10` "
         "(aggressive: uses Phantom Dive / the big toolbox attacks more)._\n",
         "## Roster\n", "| # | deck | archetype | config | vs heuristic |",
         "|---|------|-----------|--------|--------------|"]
    for i, d in enumerate(decks, 1):
        wh, arch, _ = T.META[d]
        L.append(f"| {i} | `{d}` | {arch} | {T.ROSTER[d].get('plies')}-ply"
                 f"{' aggr' if T.ROSTER[d].get('w_dmg') else ''} | {wh:.1f}% |")
    L.append("\n## Win-rate matrix (row's win% vs column)\n")
    L.append("| vs → | " + " | ".join(short[d] for d in decks) + " |")
    L.append("|------|" + "|".join("---" for _ in decks) + "|")
    for a in decks:
        cells = [" — " if a == b else f"{(win[a][b]/dec[a][b]*100 if dec[a][b] else 0):.0f}%" for b in decks]
        L.append(f"| **{short[a]}** | " + " | ".join(cells) + " |")
    L.append("\n## Overall ranking (vs the field)\n| rank | deck | win% | record |")
    L.append("|------|------|------|--------|")
    for i, (a, wr, tw, td) in enumerate(rank, 1):
        L.append(f"| {i} | `{a}` | **{wr:.1%}** | {tw}/{td} |")
    L.append("\n## Per-deck strategy\n")
    for a, wr, tw, td in rank:
        wh, arch, strat = T.META[a]
        L.append(f"### {a} — {arch}\n_Field: **{wr:.1%}** · {wh:.1f}% vs heuristic_\n\n{strat}\n")
    os.makedirs("tournaments", exist_ok=True)
    open("tournaments/8_deck_tourney.md", "w", encoding="utf-8").write("\n".join(L))
    print("\n=== FINAL RANKING ===")
    for i, (a, wr, tw, td) in enumerate(rank, 1):
        print(f"  {i}. {a:<22} {wr:.1%}")
    print("Wrote tournaments/8_deck_tourney.md")


def main():
    idx = int(sys.argv[1])
    decks = list(T.ROSTER)
    pairs = list(itertools.combinations(decks, 2))
    batch = pairs[idx * BATCH:(idx + 1) * BATCH]
    if idx == 0 and os.path.exists(ACC):
        os.remove(ACC)
    print(f"=== ROUND {idx+1}/4 — {len(batch)} pairs (n={N}) ===")
    with ProcessPoolExecutor(max_workers=12) as ex, open(ACC, "a") as f:
        for dA, dB in batch:
            t0 = time.perf_counter()
            wa, wb = run_pair(ex, dA, dB)
            f.write(f"{dA} {dB} {wa} {wb}\n"); f.flush()
            wr = wa / (wa + wb) if (wa + wb) else 0
            print(f"  {dA:<20} vs {dB:<20} {wr:>5.0%} ({wa}-{wb}) [{time.perf_counter()-t0:.0f}s]", flush=True)
    if idx == 3:
        build_report(decks)
    print(f"ROUND {idx+1}/4 COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
