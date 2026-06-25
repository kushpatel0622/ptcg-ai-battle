"""Extract every distinct deck used in the downloaded replays into decks/.

Each replay carries both players' 60-card decks (the deck-selection actions).
These are legal, ladder-tested lists, so they make a great candidate pool for
our multi-deck arena. We dedup identical decks and name each by its signature
(highest-HP) Pokémon.

Run:  python scripts/extract_replay_decks.py
"""
import collections
import glob
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import engine  # noqa: E402,F401
from cg.api import CardType, all_card_data  # noqa: E402
from rl.replays import parse_episode  # noqa: E402

cards = {c.cardId: c for c in all_card_data()}
DECKS_DIR = os.path.join(REPO, "decks")
REPLAY_DIR = os.path.join(REPO, "data", "replays")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def deck_name(deck) -> str:
    """Signature = the highest-HP Pokémon in the deck."""
    poke = [(cards[c].hp, cards[c].name) for c in set(deck)
            if cards.get(c) and int(cards[c].cardType) == CardType.POKEMON]
    if not poke:
        return "deck"
    return slug(max(poke)[1])


def summarize(deck) -> str:
    cnt = collections.Counter(deck)
    basics = sum(n for c, n in cnt.items()
                 if cards.get(c) and int(cards[c].cardType) == CardType.POKEMON and cards[c].basic)
    energy = sum(n for c, n in cnt.items() if cards.get(c) and int(cards[c].cardType) in (5, 6))
    top = [cards[c].name for c, _ in cnt.most_common()
           if cards.get(c) and int(cards[c].cardType) == CardType.POKEMON][:3]
    return f"basics={basics} energy={energy} key={', '.join(top)}"


def main() -> int:
    os.makedirs(DECKS_DIR, exist_ok=True)
    seen = {}  # sorted-tuple -> name
    names = collections.Counter()
    files = sorted(glob.glob(os.path.join(REPLAY_DIR, "*.json")))
    for path in files:
        ep = parse_episode(path)
        for deck in (ep["decks"] or []):
            if not deck or len(deck) != 60:
                continue
            key = tuple(sorted(deck))
            if key in seen:
                continue
            base = deck_name(deck)
            names[base] += 1
            name = base if names[base] == 1 else f"{base}_{names[base]}"
            seen[key] = name
            with open(os.path.join(DECKS_DIR, f"{name}.csv"), "w") as f:
                f.write("\n".join(str(x) for x in deck) + "\n")
            print(f"  {name:28s} {summarize(deck)}")

    print(f"\nExtracted {len(seen)} distinct decks -> {DECKS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
