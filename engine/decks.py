"""Deck loading helpers."""
from __future__ import annotations

import os

from . import REPO_ROOT, SUBMISSION_DIR

DEFAULT_DECK_PATH = os.path.join(SUBMISSION_DIR, "deck.csv")
DECKS_DIR = os.path.join(REPO_ROOT, "decks")


def named_deck(name: str) -> list[int]:
    """Load a deck by name from decks/ (searches subfolders like top10/, testideas/).
    The '.csv' suffix is optional."""
    import glob

    fname = name if name.endswith(".csv") else name + ".csv"
    direct = os.path.join(DECKS_DIR, fname)
    if os.path.exists(direct):
        return load_deck(direct)
    matches = glob.glob(os.path.join(DECKS_DIR, "**", fname), recursive=True)
    if not matches:
        raise FileNotFoundError(f"deck '{name}' not found under {DECKS_DIR}")
    return load_deck(matches[0])


def legalize_deck(card_ids, db, pad_energy_id: int = 3) -> list[int]:
    """Force a card-id list to satisfy the hard deck rules so an LLM can focus on
    strategy: drop unknown ids, clamp non-Basic-Energy cards to <=4 copies, keep
    at most 1 ACE SPEC, and pad/trim to exactly 60 (padding with the deck's own
    most-common Basic Energy, else ``pad_energy_id``). Does NOT fix evolution
    orphans — battle_start still validates those."""
    from cg.api import CardType  # local import to avoid cycles

    out: list[int] = []
    counts: dict[int, int] = {}
    ace = 0
    for cid in card_ids:
        c = db.card(cid)
        if c is None:
            continue
        if c.aceSpec:
            if ace >= 1:
                continue
            ace += 1
            out.append(cid)
        elif int(c.cardType) == CardType.BASIC_ENERGY:
            out.append(cid)
        else:
            if counts.get(cid, 0) >= 4:
                continue
            counts[cid] = counts.get(cid, 0) + 1
            out.append(cid)
    if len(out) > 60:
        out = out[:60]
    if len(out) < 60:
        be = [x for x in out if db.card(x) and int(db.card(x).cardType) == CardType.BASIC_ENERGY]
        pad = max(set(be), key=be.count) if be else pad_energy_id
        out += [pad] * (60 - len(out))
    return out


def load_deck(path: str) -> list[int]:
    with open(path) as f:
        return [int(x) for x in f.read().split() if x.strip()]


_DEFAULT: list[int] | None = None


def default_deck() -> list[int]:
    """The deck in submission/deck.csv (cached)."""
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = load_deck(DEFAULT_DECK_PATH)
    return _DEFAULT
