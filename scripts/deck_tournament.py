"""Deck-vs-deck tournament: every candidate deck (including the replay decks from
the JSON battle history) plays every other, piloted by the SAME fixed agent
(heuristic) so the result isolates DECK strength. Alternating seats.

Writes a human-readable fight log to the repo's sims/ folder:
  - sims/SIMULATIONS_LOG.md           (append-only one-line index of every run)
  - sims/deck_tournament_<stamp>.md   (full standings + win matrix for this run)

Run:  python scripts/deck_tournament.py -n 12
"""
import argparse
import glob
import itertools
import os
import sys
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import engine  # noqa: E402,F401
from baselines.heuristic_agent import heuristic_agent  # noqa: E402
from engine.decks import load_deck  # noqa: E402
from engine.harness import play_match  # noqa: E402

SIMS = os.path.join(REPO, "sims")
# decks that came from the provided JSON battle-history replays
REPLAY_DECKS = {"mega_starmie_ex", "mega_starmie_ex_2", "mega_starmie_ex_3", "walrein", "fezandipiti_ex"}


def source(name):
    return "replay" if name in REPLAY_DECKS else "designed"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games", type=int, default=12, help="games per pairing")
    args = ap.parse_args()

    paths = sorted(glob.glob(os.path.join(REPO, "decks", "**", "*.csv"), recursive=True))
    decks = {os.path.splitext(os.path.basename(p))[0]: load_deck(p) for p in paths}
    names = sorted(decks)
    print(f"Tournament: {len(names)} decks, {args.games} games/pair, heuristic pilot "
          f"({len(names) * (len(names) - 1) // 2} pairings)...")

    matrix = {a: {} for a in names}
    tot = {a: {"w": 0, "g": 0} for a in names}
    errors = 0
    for a, b in itertools.combinations(names, 2):
        res = play_match(heuristic_agent, heuristic_agent, decks[a], decks[b],
                         n_games=args.games, alternate=True)
        wa, wb = res["wins_a"], res["wins_b"]
        errors += res["errors"]
        g = wa + wb
        matrix[a][b], matrix[b][a] = wa, wb
        tot[a]["w"] += wa; tot[a]["g"] += g
        tot[b]["w"] += wb; tot[b]["g"] += g
        print(f"  {a} vs {b}: {wa}-{wb}")

    def winrate(n):
        return tot[n]["w"] / tot[n]["g"] if tot[n]["g"] else 0.0
    standings = sorted(names, key=lambda n: -winrate(n))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(SIMS, exist_ok=True)
    detail = os.path.join(SIMS, f"deck_tournament_{stamp}.md")
    lines = [f"# Deck tournament — {datetime.now():%Y-%m-%d %H:%M}",
             f"\n{len(names)} decks · {args.games} games/pair · heuristic pilot (fixed) · "
             f"alternating seats · errors={errors}\n",
             "## Standings (by win-rate vs the field)\n",
             "| # | Deck | Win% | W | G | Source |", "|--:|------|-----:|--:|--:|--------|"]
    for i, n in enumerate(standings, 1):
        lines.append(f"| {i} | {n} | {winrate(n):.0%} | {tot[n]['w']} | {tot[n]['g']} | {source(n)} |")
    lines.append("\n## Win matrix (row's wins vs column, out of "
                 f"{args.games})\n")
    lines.append("| vs | " + " | ".join(n[:10] for n in standings) + " |")
    lines.append("|----|" + "----|" * len(standings))
    for r in standings:
        cells = []
        for c in standings:
            cells.append("·" if r == c else str(matrix[r].get(c, "")))
        lines.append(f"| {r[:14]} | " + " | ".join(cells) + " |")
    with open(detail, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    champ = standings[0]
    log = os.path.join(SIMS, "SIMULATIONS_LOG.md")
    new = not os.path.exists(log)
    with open(log, "a", encoding="utf-8") as f:
        if new:
            f.write("# Simulations / fights log\n\nAppend-only index of every in-house simulation run. "
                    "Detailed results are in the per-run files in this folder.\n\n"
                    "| When | Type | Setup | Result | Detail |\n|------|------|-------|--------|--------|\n")
        f.write(f"| {datetime.now():%Y-%m-%d %H:%M} | deck-tournament | {len(names)} decks, "
                f"{args.games} g/pair, heuristic pilot | **{champ}** wins ({winrate(champ):.0%}) | "
                f"[{os.path.basename(detail)}]({os.path.basename(detail)}) |\n")

    print(f"\n=== Champion: {champ} ({winrate(champ):.0%}) ===")
    print("Top 5:", ", ".join(f"{n} {winrate(n):.0%}" for n in standings[:5]))
    print(f"Wrote {detail} and updated sims/SIMULATIONS_LOG.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
