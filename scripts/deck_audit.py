"""Mechanical deck auditor — checks the factors that make a deck actually FUNCTION
(beyond mere 60-card legality, which the engine checks):

  - Evolution lines: every Stage 1/2 has a real path into play (its pre-evolution
    in-deck, or Rare Candy + the Basic for a Stage 2). Flags UNCASTABLE orphans.
  - Stage depth: how many evolution steps the attackers need (1/2 stages = slower).
  - Energy feasibility: the deck's energy types can actually pay every attacker's
    attack cost (colored symbols), accounting for Colorless = any + special energy.
  - Attack economy: energy count vs the heaviest attack cost (can it power up?).
  - Type matchups: each attacker's type, Weakness and Resistance (exposure).

Run:  python scripts/deck_audit.py                 # audit every deck in decks/**
      python scripts/deck_audit.py --deck decks/top10/starmie_aggro.csv
"""
import argparse
import collections
import glob
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import engine  # noqa: F401
from cg.api import CardType, EnergyType, all_attack, all_card_data  # noqa: E402
from engine.decks import load_deck  # noqa: E402

CARDS = {c.cardId: c for c in all_card_data()}
ATKS = {a.attackId: a for a in all_attack()}
BY_NAME = {c.name: c for c in CARDS.values()}
ELET = {0: "C", 1: "G", 2: "R", 3: "W", 4: "L", 5: "P", 6: "F", 7: "D", 8: "M", 9: "N", 10: "Y", 11: "T"}


def en(t):
    return ELET.get(int(t), "-") if t is not None else "-"


def cost(a):
    return "".join(en(e) for e in a.energies) or "-"


def audit(deck):
    cnt = collections.Counter(deck)
    poke = [(cid, n) for cid, n in cnt.items()
            if CARDS.get(cid) and int(CARDS[cid].cardType) == CardType.POKEMON]
    deck_names = {CARDS[cid].name for cid, _ in poke}
    has_candy = any(CARDS.get(cid) and CARDS[cid].name == "Rare Candy" for cid in cnt)
    basic_types = {int(CARDS[cid].energyType) for cid in cnt
                   if CARDS.get(cid) and int(CARDS[cid].cardType) == CardType.BASIC_ENERGY}
    has_special = any(CARDS.get(cid) and int(CARDS[cid].cardType) == CardType.SPECIAL_ENERGY for cid in cnt)
    energy_n = sum(n for cid, n in cnt.items()
                   if CARDS.get(cid) and int(CARDS[cid].cardType) in (5, 6))

    def castable(c):
        if c.basic:
            return True
        pre = c.evolvesFrom
        if not pre:
            return True
        if pre in deck_names:  # hard evolve from the in-deck previous stage
            return True
        if c.stage2 and has_candy:  # Rare Candy skip: need the Basic in deck
            s1 = BY_NAME.get(pre)
            basic = s1.evolvesFrom if s1 else None
            if basic is None and s1 and s1.basic:
                return True
            if basic and basic in deck_names:
                return True
        return False

    flags, orphans, energy_miss = [], [], []
    stages = collections.Counter()
    for cid, n in poke:
        c = CARDS[cid]
        stages["B" if c.basic else ("S1" if c.stage1 else ("S2" if c.stage2 else "?"))] += n
        if not castable(c):
            orphans.append(f"{c.name} (needs {c.evolvesFrom or '?'})")

    # energy feasibility for castable attackers
    attackers = []
    for cid, n in poke:
        c = CARDS[cid]
        if not c.attacks or not castable(c):
            continue
        best = max((ATKS[a] for a in c.attacks if a in ATKS), key=lambda a: a.damage, default=None)
        if best is None:
            continue
        attackers.append((c, best))
        # an attacker is "dead" only if NONE of its attacks are payable by the deck's energy
        payable, needs = False, set()
        for a in c.attacks:
            atk = ATKS.get(a)
            if not atk:
                continue
            gaps = [int(e) for e in atk.energies
                    if int(e) != EnergyType.COLORLESS and int(e) not in basic_types and not has_special]
            if gaps:
                needs.update(gaps)
            else:
                payable = True
        if not payable and needs:
            energy_miss.append(f"{c.name}: no payable attack (needs {'/'.join(en(t) for t in sorted(needs))})")

    if orphans:
        flags.append(f"UNCASTABLE evolutions: {len(orphans)}")
    if energy_miss:
        flags.append(f"energy-type mismatch: {len(set(energy_miss))}")
    if stages["B"] < 8:
        flags.append(f"low Basics ({stages['B']})")
    max_cost = max((len(b.energies) for _, b in attackers), default=0)
    if energy_n < 8 and max_cost >= 2:
        flags.append(f"thin energy ({energy_n}) for cost {max_cost}")
    if stages["S2"] >= 6 and not has_candy:
        flags.append("Stage-2 heavy without Rare Candy (slow)")

    return {"stages": stages, "basic_types": sorted(en(t) for t in basic_types), "special": has_special,
            "energy_n": energy_n, "orphans": orphans, "energy_miss": sorted(set(energy_miss)),
            "attackers": attackers, "max_cost": max_cost, "flags": flags}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", default=None)
    args = ap.parse_args()
    paths = ([args.deck] if args.deck
             else sorted(glob.glob(os.path.join(REPO, "decks", "**", "*.csv"), recursive=True)))

    clean = 0
    for p in paths:
        name = os.path.splitext(os.path.basename(p))[0]
        a = audit(load_deck(p))
        st = a["stages"]
        print(f"\n=== {name} ===")
        print(f"  stages: B{st['B']} S1{st['S1']} S2{st['S2']} | energy: {a['energy_n']} "
              f"[{','.join(a['basic_types'])}]{'+special' if a['special'] else ''} | max attack cost: {a['max_cost']}")
        for c, b in sorted(a["attackers"], key=lambda x: -x[1].damage)[:4]:
            print(f"    {c.name} ({en(c.energyType)}, weak {en(c.weakness)}, res {en(c.resistance)}): "
                  f"{b.name} {b.damage}[{cost(b)}]")
        if a["orphans"]:
            print(f"  UNCASTABLE: {'; '.join(a['orphans'])}")
        if a["energy_miss"]:
            print(f"  ENERGY GAPS: {'; '.join(a['energy_miss'])}")
        print(f"  FLAGS: {', '.join(a['flags']) if a['flags'] else 'none — mechanically sound'}")
        clean += not a["flags"]
    print(f"\n=== {clean}/{len(paths)} decks mechanically clean ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
