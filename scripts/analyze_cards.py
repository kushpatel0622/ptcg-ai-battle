"""Programmatic study of the WHOLE card pool (not just the replay decks).

Computes the hard, data-driven facts deckbuilding needs:
  - Type matchup matrix (who is weak/resistant to whom -> which attacker types are favored).
  - Attacker efficiency (damage-per-energy, cheap aggro, one-shot big hitters, ex prize liability).
  - Trainer toolbox categorized by function (search / draw / gust / accel / denial / recovery / heal).
  - Special energy catalog and evolution-stage distribution.

Writes data/card_analysis.md (the factual backbone the card-knowledge study builds on).

Run:  python scripts/analyze_cards.py
"""
import collections
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import engine  # noqa: F401
from cg.api import CardType, EnergyType, all_attack, all_card_data  # noqa: E402

cards = {c.cardId: c for c in all_card_data()}
attacks = {a.attackId: a for a in all_attack()}
ELET = {0: "C", 1: "G", 2: "R", 3: "W", 4: "L", 5: "P", 6: "F", 7: "D", 8: "M", 9: "N", 10: "Y", 11: "T"}
TYPES = [EnergyType.GRASS, EnergyType.FIRE, EnergyType.WATER, EnergyType.LIGHTNING, EnergyType.PSYCHIC,
         EnergyType.FIGHTING, EnergyType.DARKNESS, EnergyType.METAL, EnergyType.DRAGON, EnergyType.COLORLESS]

effects = {}
with open(os.path.join(REPO, "pokemon-tcg-ai-battle", "EN_Card_Data.csv"), encoding="utf-8") as f:
    r = csv.reader(f)
    next(r)
    for row in r:
        if row and row[0].strip().isdigit():
            e = (row[16] if len(row) > 16 else "").strip()
            if e and e.lower() != "n/a":
                effects[int(row[0])] = e


def en(t):
    return ELET.get(int(t), "-") if t is not None else "-"


def prizes(c):
    return 3 if c.megaEx else (2 if c.ex else 1)


def main() -> int:
    pokemon = [c for c in cards.values() if int(c.cardType) == CardType.POKEMON]
    out = ["# Whole-pool card analysis\n",
           f"Pool: {len(cards)} engine cards "
           f"({sum(1 for c in cards.values() if int(c.cardType)==CardType.POKEMON)} Pokémon, "
           f"{sum(1 for c in cards.values() if int(c.cardType) in (1,2,3,4))} Trainers, "
           f"{sum(1 for c in cards.values() if int(c.cardType) in (5,6))} Energy).\n"]

    # --- Type matchup matrix ---
    out.append("\n## Type matchup matrix")
    out.append("For attacker type T: `exploits` = # Pokémon in the pool weak to T (take 2x); "
               "`walled_by` = # that resist T. `own_weakness` = most common weakness of T's own Pokémon.\n")
    out.append("| Type | #Pokémon | exploits(weak-to-T) | walled_by(resist-T) | own common weakness |")
    out.append("|------|---------:|--------------------:|--------------------:|---------------------|")
    weak_to = collections.Counter(en(c.weakness) for c in pokemon if c.weakness is not None)
    resist_to = collections.Counter(en(c.resistance) for c in pokemon if c.resistance is not None)
    for t in TYPES:
        L = ELET[int(t)]
        own = [en(c.weakness) for c in pokemon if int(c.energyType) == int(t) and c.weakness is not None]
        common = collections.Counter(own).most_common(1)
        n_own = sum(1 for c in pokemon if int(c.energyType) == int(t))
        out.append(f"| {EnergyType(t).name} ({L}) | {n_own} | {weak_to.get(L,0)} | {resist_to.get(L,0)} "
                   f"| {common[0][0] if common else '-'} |")

    # --- Attacker efficiency ---
    def atk_rows():
        rows = []
        for c in pokemon:
            for aid in c.attacks:
                a = attacks.get(aid)
                if not a or a.damage <= 0:
                    continue
                cost = len(a.energies)
                if cost == 0:
                    continue
                rows.append((a.damage / cost, a.damage, cost, "".join(en(e) for e in a.energies),
                             c.name, en(c.energyType), prizes(c), c.hp))
        return rows
    rows = atk_rows()
    out.append("\n## Most energy-efficient attackers (damage ÷ energy cost)")
    out.append("| dmg/E | dmg | cost | type | HP | prizes | Pokémon |")
    out.append("|------:|----:|------|------|---:|-------:|---------|")
    for dpe, dmg, cost, costs, name, typ, pz, hp in sorted(rows, reverse=True)[:30]:
        out.append(f"| {dpe:.0f} | {dmg} | {costs}({cost}) | {typ} | {hp} | {pz} | {name} |")

    out.append("\n## Cheap aggro (≥90 dmg for ≤2 energy)")
    cheap = sorted([r for r in rows if r[1] >= 90 and r[2] <= 2], reverse=True)[:20]
    for dpe, dmg, cost, costs, name, typ, pz, hp in cheap:
        out.append(f"- {name} ({typ}, HP{hp}, {pz}pz): {dmg} for {costs}")

    out.append("\n## One-shot big hitters (≥250 dmg)")
    big = sorted([r for r in rows if r[1] >= 250], key=lambda r: -r[1])[:20]
    for dpe, dmg, cost, costs, name, typ, pz, hp in big:
        out.append(f"- {name} ({typ}, HP{hp}, {pz}pz): {dmg} for {costs}({cost})")

    # --- Trainer toolbox by function ---
    CATS = [
        ("Pokémon search", lambda e: "search your deck" in e and ("pokémon" in e or "basic" in e)),
        ("Energy search", lambda e: "search your deck" in e and "energy" in e),
        ("Draw", lambda e: "draw" in e),
        ("Gust (drag up opponent)", lambda e: "opponent" in e and ("benched" in e and "active spot" in e)),
        ("Switch (your own)", lambda e: "switch your active" in e),
        ("Energy acceleration", lambda e: "attach" in e and "energy" in e and ("deck" in e or "discard" in e)),
        ("Energy denial", lambda e: "discard" in e and "opponent" in e and "energy" in e),
        ("Recovery (from discard)", lambda e: "discard pile" in e and ("hand" in e or "deck" in e or "bench" in e)),
        ("Healing", lambda e: "heal" in e or "remove" in e and "damage counter" in e),
    ]
    out.append("\n## Trainer toolbox (by function)")
    for label, fn in CATS:
        hits = [(cid, cards[cid].name, effects[cid]) for cid in effects
                if cid in cards and int(cards[cid].cardType) in (1, 2, 3, 4) and fn(effects[cid].lower())]
        out.append(f"\n### {label} ({len(hits)})")
        for cid, name, eff in hits[:10]:
            ace = " [ACE SPEC]" if cards[cid].aceSpec else ""
            out.append(f"- [{cid}] {name}{ace}: {eff[:120]}")

    # --- Special energy ---
    out.append("\n## Special Energy")
    for cid, c in cards.items():
        if int(c.cardType) == CardType.SPECIAL_ENERGY:
            out.append(f"- [{cid}] {c.name}: {effects.get(cid, '')[:130]}")

    # --- Stage distribution ---
    out.append("\n## Evolution-stage distribution (Pokémon by type × stage)")
    out.append("| Type | Basic | Stage1 | Stage2 |")
    out.append("|------|------:|-------:|-------:|")
    for t in TYPES:
        ps = [c for c in pokemon if int(c.energyType) == int(t)]
        b = sum(1 for c in ps if c.basic)
        s1 = sum(1 for c in ps if c.stage1)
        s2 = sum(1 for c in ps if c.stage2)
        out.append(f"| {EnergyType(t).name} | {b} | {s1} | {s2} |")

    path = os.path.join(REPO, "data", "card_analysis.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"wrote {path} ({len(out)} lines, {os.path.getsize(path)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
