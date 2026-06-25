"""Build a curated, type-organized digest of the card pool for LLM deck design.

Includes the strongest Pokemon per type (HP, stage/evolution line, weakness,
resistance, retreat, top attacks + energy costs) and the key trainers/energy,
so a reasoning model can design decks around battle strategy, type matchups, and
card optimization. Writes data/card_digest.md.

Run:  python scripts/card_digest.py
"""
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
TYPES = [EnergyType.GRASS, EnergyType.FIRE, EnergyType.WATER, EnergyType.LIGHTNING,
         EnergyType.PSYCHIC, EnergyType.FIGHTING, EnergyType.DARKNESS, EnergyType.METAL,
         EnergyType.DRAGON, EnergyType.COLORLESS]

# trainer effect text from the CSV
effects = {}
with open(os.path.join(REPO, "pokemon-tcg-ai-battle", "EN_Card_Data.csv"), encoding="utf-8") as f:
    r = csv.reader(f)
    next(r)
    for row in r:
        if row and row[0].strip().isdigit():
            cid = int(row[0])
            eff = (row[16] if len(row) > 16 else "").strip()
            if eff and eff.lower() != "n/a":
                effects[cid] = eff[:150]


def en(t):
    return ELET.get(int(t), "?") if t is not None else "-"


def cost(atk):
    return "".join(en(e) for e in atk.energies) or "-"


def atk_lines(c):
    if not c.attacks:
        return "no attack"
    aa = sorted((attacks[a] for a in c.attacks if a in attacks), key=lambda a: -a.damage)[:2]
    return "; ".join(f"{a.name} {a.damage}[{cost(a)}]" for a in aa)


def stage(c):
    return "Basic" if c.basic else ("St1" if c.stage1 else ("St2" if c.stage2 else "?"))


def main() -> int:
    out = ["# Card pool digest (for deck design)\n",
           "Format: [id] Name (Stage, HP, weak=W, res=R, retreat=N): attacks Name DMG[cost]. "
           "Energy letters: C G(rass) R(fire) W(ater) L(ightning) P(sychic) F(ighting) D(ark) M(etal) N=dragon Y=rainbow.\n"]

    out.append("\n## Pokémon by type (top attackers)\n")
    for t in TYPES:
        pool = [c for c in cards.values()
                if int(c.cardType) == CardType.POKEMON and c.hp >= 110 and int(c.energyType) == int(t)]
        pool.sort(key=lambda c: (-int(bool(c.ex or c.megaEx)), -c.hp))
        if not pool:
            continue
        out.append(f"\n### {EnergyType(t).name}")
        for c in pool[:10]:
            tag = "MegaEX" if c.megaEx else ("EX" if c.ex else "")
            ev = f" <-{c.evolvesFrom}" if c.evolvesFrom else ""
            abil = f" ABILITY:{c.skills[0].name}" if c.skills else ""
            out.append(f"- [{c.cardId}] {c.name} {tag} ({stage(c)}, HP{c.hp}, weak={en(c.weakness)}, "
                       f"res={en(c.resistance)}, rt{c.retreatCost}{ev}): {atk_lines(c)}{abil}")

    out.append("\n## Key Trainers (search / draw / switch / disruption / tools)\n")
    kw = ("search your deck", "draw", "switch", "knocked out", "damage counter", "discard",
          "from your hand", "heal", "energy", "prevent", "prize")
    shown = 0
    for cid, c in cards.items():
        if int(c.cardType) in (CardType.ITEM, CardType.SUPPORTER, CardType.STADIUM, CardType.TOOL):
            eff = effects.get(cid, "")
            if eff and any(k in eff.lower() for k in kw):
                typ = ["Pokemon", "Item", "Tool", "Supporter", "Stadium"][int(c.cardType)] if int(c.cardType) <= 4 else "?"
                ace = " [ACE SPEC]" if c.aceSpec else ""
                out.append(f"- [{cid}] {c.name} ({typ}){ace}: {eff}")
                shown += 1
        if shown >= 70:
            break

    out.append("\n## Special Energy\n")
    for cid, c in cards.items():
        if int(c.cardType) == CardType.SPECIAL_ENERGY:
            out.append(f"- [{cid}] {c.name}: {effects.get(cid, '')}")
    out.append("\n## Basic Energy: [1]=Grass [2]=Fire [3]=Water [4]=Lightning "
               "[5]=Psychic [6]=Fighting [7]=Darkness [8]=Metal (use any count, no 4-copy limit)\n")

    path = os.path.join(REPO, "data", "card_digest.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"wrote {path}  ({len(out)} lines, {os.path.getsize(path)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
