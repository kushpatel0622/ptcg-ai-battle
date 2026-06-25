"""Explore the engine-known card pool to inform deckbuilding.

Cross-references all_card_data() (the 1267 cards the engine actually supports)
with EN_Card_Data.csv (human-readable names + effect text), and prints
candidate Basic Pokémon and consistency trainers (search/draw/switch).

Run:  python scripts/explore_cards.py
"""
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import engine  # noqa: F401
from cg.api import CardType, EnergyType, all_attack, all_card_data  # noqa: E402

CSV = os.path.join(REPO, "pokemon-tcg-ai-battle", "EN_Card_Data.csv")

cards = {c.cardId: c for c in all_card_data()}
attacks = {a.attackId: a for a in all_attack()}

# id -> human info from CSV (aggregate rows per card)
info: dict[int, dict] = {}
with open(CSV, encoding="utf-8") as f:
    r = csv.reader(f)
    next(r)
    for row in r:
        if not row or not row[0].strip().isdigit():
            continue
        cid = int(row[0])
        d = info.setdefault(cid, {"name": row[1], "stage": row[4], "cat": row[6],
                                  "type": row[9], "retreat": row[12], "effects": set()})
        eff = (row[16] if len(row) > 16 else "").strip()
        if eff and eff.lower() != "n/a":
            d["effects"].add(eff)


def nm(cid):
    return info.get(cid, {}).get("name", f"#{cid}")


def best_atk(c):
    if not c.attacks:
        return None
    aid = max(c.attacks, key=lambda a: attacks[a].damage if a in attacks else 0)
    return attacks.get(aid)


def cost_str(atk):
    return "".join({0:"C",1:"G",2:"R",3:"W",4:"L",5:"P",6:"F",7:"D",8:"M",9:"N",10:"Y",11:"T"}.get(int(e), "?")
                   for e in atk.energies)


print("=== Basic WATER Pokémon (engine-known), by HP ===")
basics_w = [c for c in cards.values()
            if c.cardType == CardType.POKEMON and c.basic and c.energyType == EnergyType.WATER]
for c in sorted(basics_w, key=lambda c: -c.hp)[:22]:
    a = best_atk(c)
    atk = f"{a.name} {a.damage}dmg [{cost_str(a)}]" if a else "(no attack)"
    flags = "EX" if c.ex else ""
    print(f"  {c.cardId:5d} {nm(c.cardId)[:24]:24s} HP{c.hp:3d} rt{c.retreatCost} {flags:2s} | {atk}")

print("\n=== Basic Pokémon (any type) WITH abilities (utility/consistency) ===")
util = [c for c in cards.values() if c.cardType == CardType.POKEMON and c.basic and c.skills]
for c in sorted(util, key=lambda c: -c.hp)[:18]:
    sk = "; ".join(s.name for s in c.skills)
    et = EnergyType(c.energyType).name[:5]
    print(f"  {c.cardId:5d} {nm(c.cardId)[:22]:22s} HP{c.hp:3d} {et:5s} | ability: {sk[:60]}")

print("\n=== ITEM cards that search the DECK (consistency) ===")
n = 0
for cid, d in info.items():
    if cid not in cards or d["stage"] != "Item":
        continue
    txt = " ".join(d["effects"]).lower()
    if "search your deck" in txt:
        print(f"  {cid:5d} {d['name'][:26]:26s} | {' '.join(d['effects'])[:90]}")
        n += 1
        if n >= 16:
            break

print("\n=== SUPPORTER cards that DRAW ===")
n = 0
for cid, d in info.items():
    if cid not in cards or d["stage"] != "Supporter":
        continue
    txt = " ".join(d["effects"]).lower()
    if "draw" in txt:
        print(f"  {cid:5d} {d['name'][:24]:24s} | {' '.join(d['effects'])[:90]}")
        n += 1
        if n >= 16:
            break

print("\n=== SWITCH / gust effects (Item/Supporter) ===")
n = 0
for cid, d in info.items():
    if cid not in cards or d["stage"] not in ("Item", "Supporter"):
        continue
    txt = " ".join(d["effects"]).lower()
    if "switch" in txt:
        print(f"  {cid:5d} {d['name'][:24]:24s} [{d['stage']}] | {' '.join(d['effects'])[:80]}")
        n += 1
        if n >= 12:
            break
