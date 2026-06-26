"""8-deck round-robin tournament (agent-vs-agent = real-competition proxy).

Every deck is piloted by the SAME search agent (SearchTeacher) at its best per-deck
config: 2-ply where it helps (the agent evaluates EVERY legal option and scores each
by the opponent's reply, so it plays DEFENSIVELY — it won't leave its attacker open to
a return KO if a safer line preserves it) plus the dynamic_attack fix (it plays the
heuristic-invisible dynamic-damage attacks). Both sides use the same agent, so the
matchups measure DECK strength + piloting against a PEER — unlike the vs-heuristic
benchmark (which the heuristic mispilots).

Writes a full report to tournaments/8_deck_tourney.md.

Run:  python scripts/exp_tournament.py -n 240
"""
from __future__ import annotations

import argparse
import itertools
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# deck -> best config (per-deck plies; samples=1, dynamic_attack=True, generic opp for all)
ROSTER = {
    "fighting_pivot":       dict(plies=2),
    "single_prize_control": dict(plies=2),
    "mega_starmie_ex_2":    dict(plies=2),
    "starmie_aggro":        dict(plies=2),
    "dragapult_dusknoir":   dict(plies=2, w_dmg=10),   # aggressive: use Phantom Dive/big attacks
    "ns_zoroark_toolbox":   dict(plies=2, w_dmg=10),   # aggressive: best config (16.9% vs aggro)
    "lightning_counter":    dict(plies=2),
    "mega_starmie_ex":      dict(plies=1),
}

# vs-heuristic win% (best config, large-n) + archetype + strategy, for the report.
META = {
    "fighting_pivot": (85.4, "Fighting / Mega Lucario ex aggro-toolbox",
        "Mega Lucario ex (340 HP, Mega-evolves from Riolu) is a one-Prize-efficient beater; "
        "Flygon ex / Fezandipiti ex / Meowth ex add dynamic-damage attacks (Cruel Arrow = 100 "
        "snipe to any Pokémon, Sonic Peridot = 100 to each opposing ex) that the heuristic scores "
        "as 0 and never plays. 33-card trainer engine. Wins by relentless efficient attacks plus "
        "picking off key targets; the dynamic_attack fix makes it our strongest deck vs the heuristic."),
    "single_prize_control": (86.5, "Water Walrein single-prize control",
        "Spheal→Sealeo→Walrein walls (single-Prize attackers, so the opponent must score six KOs while "
        "we trade up) backed by Dunsparce/Dudunsparce draw. Grinds the game out; 2-ply's defensive read "
        "— keep the wall alive to attack again — is decisive."),
    "mega_starmie_ex_2": (80.1, "Water dual Mega (Starmie + Froslass) ex",
        "Two 1-energy Mega ex attackers: Mega Starmie ex (Jetting Blow 120 + 50 bench snipe / Nebula "
        "Beam 210 ignores effects) and Mega Froslass ex (Resentful Refrain = 50× opponent hand size, "
        "invisible to the heuristic). 8 basics for consistency — a fast, flexible 1-energy tempo deck."),
    "starmie_aggro": (78.9, "Water Mega Starmie ex pure aggro",
        "4 Mega Starmie ex + 4 Budew: the fastest 1-energy clock, with Budew slowing the opponent's "
        "Item-based setup. A glass-cannon prize race."),
    "dragapult_dusknoir": (88.1, "Dragapult ex / Dusknoir spread-combo",
        "Dreepy→Drakloak (Recon Directive draw)→Dragapult ex (Phantom Dive 200 + 6-counter bench spread) "
        "with the Dusclops/Dusknoir Cursed Blast engine (place 13 counters, self-KO) and Munkidori "
        "(Adrena-Brain damage-move) to hit exact KO math. Rare Candy for Stage-2 speed; Judge/Unfair Stamp "
        "disruption. A Stage-2 COMBO that the search plays tactically (immediate damage) more than as the "
        "multi-turn spread/prize-race the deck is built for."),
    "ns_zoroark_toolbox": (86.1, "N's Zoroark ex Darkness toolbox",
        "N's Zorua→N's Zoroark ex (Trade = discard 1/draw 2; Night Joker = copy a benched N's attack) "
        "powers a toolbox — N's Darmanitan snipe (Back Draft 30× opp energy), N's Reshiram / Zekrom, and "
        "Bloodmoon Ursaluna ex (Blood Moon 240) — off mono-Darkness energy. Munkidori damage-move, "
        "Pecharunt ex + Air Balloon + N's Castle mobility, Judge disruption. 1-Prize attackers force bad "
        "trades. Heavily combo-dependent (Night Joker is the whole attack engine)."),
    "lightning_counter": (75.4, "Lightning anti-Water tech",
        "Pikachu ex + Mega Manectric ex (330 HP) with Eelektrik energy acceleration, exploiting the "
        "Water-heavy meta's Lightning weakness. Slower to set up (heavy energy + evolution lines), so "
        "it is our lowest non-brick deck."),
    "mega_starmie_ex": (71.2, "Water pure Mega Starmie ex aggro (dominant replay/meta deck)",
        "The most-played ladder deck — blazing fast but inconsistent: only 3 true basics (Staryu) plus "
        "4 unplayable line-less Cinderace, so it bricks often. Best at 1-ply (2-ply's extra rollout adds "
        "noise on a deck that bricks)."),
}


def _build(deck_name, seed):
    import engine  # noqa: F401
    from engine.decks import named_deck
    from rl.search_teacher import SearchTeacher
    deck = named_deck(deck_name)
    cfg = dict(ROSTER[deck_name])
    return SearchTeacher(deck=deck, rng=random.Random(seed), samples=1,
                         dynamic_attack=True, **cfg), deck


def _run_chunk(args):
    dA, dB, n, seed = args
    import engine  # noqa: F401
    from engine.harness import play_match
    random.seed(seed)
    a, deckA = _build(dA, seed)
    b, deckB = _build(dB, seed + 10_000)
    # Cap per-game length: a pathological non-terminating mirror game would
    # otherwise spin a 2-ply search for ~100k steps and hang the whole pool.
    # 4000 decisions >> a normal game (~300); over-long games raise -> counted
    # as an error by play_match and skipped.
    res = play_match(a, b, deckA, deckB, n_games=n, max_steps=4000)
    return res["wins_a"], res["wins_b"], res["draws"], res["errors"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games", type=int, default=240)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=12)
    ap.add_argument("--out", default="tournaments/8_deck_tourney.md")
    args = ap.parse_args()

    decks = list(ROSTER)
    win = {a: {b: 0 for b in decks} for a in decks}
    dec = {a: {b: 0 for b in decks} for a in decks}

    print(f"=== Round-robin: {len(decks)} decks, n={args.games}/pair ===")
    t_all = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for dA, dB in itertools.combinations(decks, 2):
            t0 = time.perf_counter()
            jobs, remaining, k = [], args.games, 0
            while remaining > 0:
                c = min(args.chunk, remaining)
                jobs.append((dA, dB, c, 100 + k))
                remaining -= c
                k += 1
            futs = [ex.submit(_run_chunk, j) for j in jobs]
            wa = wb = skipped = 0
            for fut in futs:
                try:
                    r = fut.result(timeout=480)  # backstop: skip a hung chunk
                    wa += r[0]; wb += r[1]
                except Exception:
                    skipped += 1  # hung/failed chunk -> drop its games, keep going
            if skipped:
                print(f"    [warn] {skipped} chunk(s) skipped (timeout) for {dA} vs {dB}")
            win[dA][dB] += wa; win[dB][dA] += wb
            dec[dA][dB] += wa + wb; dec[dB][dA] += wa + wb
            wr = wa / (wa + wb) if (wa + wb) else 0.0
            print(f"  {dA:<20} vs {dB:<20} {wr:>5.0%} ({wa}-{wb}) [{time.perf_counter()-t0:.0f}s]")

    # overall ranking
    rank = []
    for a in decks:
        tw = sum(win[a][b] for b in decks if b != a)
        td = sum(dec[a][b] for b in decks if b != a)
        rank.append((a, tw / td if td else 0.0, tw, td))
    rank.sort(key=lambda r: -r[1])

    # ---- write markdown report ----
    L = []
    L.append("# 8-Deck Round-Robin Tournament\n")
    L.append(f"_Generated by `scripts/exp_tournament.py` — {args.games} games per pair, "
             f"{len(decks)} decks, {len(decks)*(len(decks)-1)//2} matchups._\n")
    L.append("Every deck is piloted by the **same search agent** (`SearchTeacher`) at its best per-deck "
             "config. The agent evaluates **every legal option** each decision and, at 2-ply, scores each "
             "by the **opponent's reply** — so it plays **defensively**, preferring lines that keep its "
             "attacker alive to act again, and it plays the heuristic-invisible **dynamic-damage attacks** "
             "(`dynamic_attack`). Both sides use the same agent, so results measure **deck strength + "
             "piloting against a peer** — a real-competition proxy, unlike the vs-heuristic benchmark "
             "(which the heuristic mispilots).\n")

    L.append("## Roster (best config + win-rate vs the heuristic)\n")
    L.append("| # | deck | archetype | config | vs heuristic |")
    L.append("|---|------|-----------|--------|--------------|")
    for i, d in enumerate(decks, 1):
        wh, arch, _ = META[d]
        whs = f"{wh:.1f}%" if wh is not None else "see below"
        L.append(f"| {i} | `{d}` | {arch} | {ROSTER[d]['plies']}-ply | {whs} |")
    L.append("")

    short = {d: d.replace("_", " ")[:13] for d in decks}
    L.append("## Win-rate matrix (row deck's win% vs column deck)\n")
    L.append("| vs → | " + " | ".join(short[d] for d in decks) + " |")
    L.append("|------|" + "|".join("------" for _ in decks) + "|")
    for a in decks:
        cells = []
        for b in decks:
            if a == b:
                cells.append(" — ")
            else:
                d = dec[a][b]
                cells.append(f"{(win[a][b]/d*100 if d else 0):.0f}%")
        L.append(f"| **{short[a]}** | " + " | ".join(cells) + " |")
    L.append("")

    L.append("## Overall ranking (win% vs the whole field)\n")
    L.append("| rank | deck | win% vs field | record |")
    L.append("|------|------|---------------|--------|")
    for i, (a, wr, tw, td) in enumerate(rank, 1):
        L.append(f"| {i} | `{a}` | **{wr:.1%}** | {tw}/{td} |")
    L.append("")

    L.append("## Per-deck strategy\n")
    for a, wr, tw, td in rank:
        wh, arch, strat = META[a]
        whs = f"{wh:.1f}% vs heuristic" if wh is not None else "(see roster)"
        L.append(f"### {a} — {arch}")
        L.append(f"_Field win-rate: **{wr:.1%}** · {whs} · {ROSTER[a]['plies']}-ply_\n")
        L.append(strat + "\n")

    L.append("## Caveats\n")
    L.append("- The agent is identical on both sides, so this isolates **deck** strength; it is **not** "
             "the Kaggle ladder (real opponents pilot differently).")
    L.append("- vs-heuristic win-rates (roster) are inflated by the heuristic **mispiloting** these decks; "
             "field win-rates here are the fairer skill-neutral comparison.")
    L.append("- Combo decks (Dragapult, N's Zoroark) are the hardest for the search — its rollouts use the "
             "heuristic, which misplays evolution/combo setup — so their numbers are a floor, not a ceiling.")
    L.append(f"\n_Total wall time: {time.perf_counter()-t_all:.0f}s._\n")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"\nWrote report -> {args.out}")
    print("\n=== overall ranking ===")
    for i, (a, wr, tw, td) in enumerate(rank, 1):
        print(f"  {i}. {a:<22} {wr:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
