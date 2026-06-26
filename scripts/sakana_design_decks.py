"""Use Sakana (fugu) to GENERATE strategy-driven decks from a COMPACT card pool.

Lesson learned: fugu/fugu-ultra are reasoning models that choke on large prompts
(the 24KB digest hung). So we feed a tight ~4KB shortlist (top attackers + key
trainers with real ids), use the faster `fugu`, and a short timeout. Each deck
is legalized + validated in the engine; rationale -> docs/DECK_STRATEGY.md.

Run with the conda env's python:
  C:/Users/itach/miniconda3/envs/pokemon_tcg/python.exe scripts/sakana_design_decks.py
"""
import csv
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(REPO, ".env"))

import engine  # noqa: E402,F401
from cg.api import CardType, EnergyType, all_attack  # noqa: E402
from cg.game import battle_finish, battle_start  # noqa: E402
from engine.cards import get_card_db  # noqa: E402
from engine.decks import legalize_deck  # noqa: E402
from llm.providers.sakana_agent import SakanaProvider  # noqa: E402

ELET = {0: "C", 1: "G", 2: "R", 3: "W", 4: "L", 5: "P", 6: "F", 7: "D", 8: "M", 9: "N", 10: "Y", 11: "T"}


def build_pool(db) -> str:
    atks = {a.attackId: a for a in all_attack()}
    eff = {}
    with open(os.path.join(REPO, "pokemon-tcg-ai-battle", "EN_Card_Data.csv"), encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if row and row[0].strip().isdigit():
                e = (row[16] if len(row) > 16 else "").strip()
                if e and e.lower() != "n/a":
                    eff[int(row[0])] = e

    def pz(c):
        return 3 if c.megaEx else (2 if c.ex else 1)

    def cost(a):
        return "".join(ELET.get(int(x), "?") for x in a.energies) or "-"

    L = ["ATTACKERS  [id] Name TYPE HP PRIZEpz: attack dmg[cost]"]
    for t in range(1, 9):  # Grass..Metal
        pool = [c for c in db.cards.values()
                if int(c.cardType) == CardType.POKEMON and int(c.energyType) == t and c.hp >= 120]
        pool.sort(key=lambda c: (-int(bool(c.ex or c.megaEx)), -c.hp))
        for c in pool[:3]:
            ba = db.best_attack(c.cardId)
            a = atks.get(ba)
            ev = f" <-{c.evolvesFrom}" if c.evolvesFrom else ""
            L.append(f"[{c.cardId}] {c.name} {EnergyType(t).name[:4]} HP{c.hp} {pz(c)}pz{ev}: "
                     f"{a.name if a else '-'} {a.damage if a else 0}[{cost(a) if a else '-'}]")
    L.append("\nKEY TRAINERS  [id] Name: effect")
    cats = [("search your deck", "pokémon"), ("draw",), ("switch",),
            ("attach", "energy", "from"), ("discard", "opponent", "energy"), ("discard pile",)]
    seen = set()
    for kws in cats:
        n = 0
        for cid, e in eff.items():
            if cid in seen or cid not in db.cards:
                continue
            c = db.cards[cid]
            if int(c.cardType) in (1, 3, 4) and all(k in e.lower() for k in kws):
                ace = " [ACE]" if c.aceSpec else ""
                L.append(f"[{cid}] {c.name}{ace}: {e[:60]}")
                seen.add(cid)
                n += 1
                if n >= 3:
                    break
    L.append("\nSPECIAL ENERGY  [id] Name")
    for cid, c in db.cards.items():
        if int(c.cardType) == CardType.SPECIAL_ENERGY:
            L.append(f"[{cid}] {c.name}")
    L.append("BASIC ENERGY: [1]Grass [2]Fire [3]Water [4]Lightning [5]Psychic [6]Fighting "
             "[7]Darkness [8]Metal (unlimited copies).")
    return "\n".join(L)


RULES = ("Rules: exactly 60 cards; max 4 copies of any card except Basic Energy; max 1 ACE SPEC; "
         "include pre-evolutions (or Rare Candy + the Basic) for any Stage 1/2; energy must match attack "
         "costs; use ONLY ids from the pool below.")
OUT_FMT = ('Output ONLY a JSON object: {"name","concept","strategy","matchups","consistency",'
           '"key_cards":[".."],"cards":[[count,id],...]} where cards sum to 60.')
JUDGING = ("Judged on clear articulation, originality, technical soundness, consistency under repeated "
           "matches, robustness (no over-reliance on lucky openings/matchups), performance, clear concept, "
           "and key-card utilization.")

BRIEFS = [
    ("lightning_counter", "Fast, consistent LIGHTNING deck to exploit the Water (Mega Starmie ex) meta's "
                          "Lightning weakness and one-shot it, with a deep search/draw engine."),
    ("original_tech", "An ORIGINAL, technically-sound off-meta deck with a reliable (not gimmicky) plan the "
                      "Water meta is unprepared for. Prefer no-drawback efficient attackers."),
]


def parse_json(text):
    m = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None


def to_list(cards_field):
    flat = []
    for it in cards_field or []:
        try:
            if isinstance(it, (list, tuple)):
                flat += [int(it[1])] * int(it[0])
            elif isinstance(it, dict):
                flat += [int(it.get("id") or it.get("card_id"))] * int(it.get("count", 1))
        except Exception:
            pass
    return flat


def deck_legal(deck):
    try:
        obs, sd = battle_start(deck, deck)
    except Exception:
        return False
    ok = obs is not None and getattr(sd, "errorPlayer", 0) < 0
    try:
        battle_finish()
    except Exception:
        pass
    return ok


def main() -> int:
    db = get_card_db()
    pool = build_pool(db)
    print(f"compact pool: {len(pool)} chars")
    provider = SakanaProvider(model="fugu", max_tokens=1500, timeout=250)
    doc = ["# Deck strategies (designed by Sakana fugu)\n",
           "Strategy-driven decks generated by a reasoning model around distinct briefs (matchups / card "
           "optimization), legalized + validated in-engine. Written to address the judging criteria.\n"]
    legal_n = 0
    for key, brief in BRIEFS:
        print(f"\n=== Designing '{key}' ...")
        try:
            raw = provider.complete("You are a world-class competitive Pokemon TCG deckbuilder. " + JUDGING,
                                    f"BRIEF: {brief}\n\n{RULES}\n\n{OUT_FMT}\n\nPOOL:\n{pool}")
        except Exception as e:
            print(f"  FAIL: {type(e).__name__}: {str(e)[:100]}")
            continue
        data = parse_json(raw)
        if not data:
            print("  no JSON parsed")
            continue
        deck = legalize_deck(to_list(data.get("cards")), db)
        legal = deck_legal(deck)
        legal_n += int(legal)
        basics = sum(1 for c in deck if db.card(c) and int(db.card(c).cardType) == CardType.POKEMON and db.card(c).basic)
        with open(os.path.join(REPO, "decks", f"sakana_{key}.csv"), "w") as f:
            f.write("\n".join(str(x) for x in deck) + "\n")
        print(f"  {data.get('name', key)}: legal={legal} basics={basics} -> decks/sakana_{key}.csv")
        doc += [f"\n## sakana_{key} — {data.get('name', key)} (legal={legal}, basics={basics})",
                f"**Concept:** {data.get('concept', '')}",
                f"**Strategy:** {data.get('strategy', '')}",
                f"**Matchups:** {data.get('matchups', '')}",
                f"**Consistency/robustness:** {data.get('consistency', '')}",
                "**Key cards:** " + "; ".join(data.get("key_cards", []) if isinstance(data.get("key_cards"), list) else [])]
    with open(os.path.join(REPO, "docs", "DECK_STRATEGY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(doc) + "\n")
    print(f"\n=== {legal_n}/{len(BRIEFS)} legal. Rationale -> docs/DECK_STRATEGY.md ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
