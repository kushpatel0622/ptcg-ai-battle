"""Card / attack metadata lookup built from the engine.

``all_card_data()`` / ``all_attack()`` return every card and attack the engine
knows about. We index them by id and expose small helpers used by the baseline
heuristic and (later) the observation encoder. Built once and cached.
"""
from __future__ import annotations

import numpy as np

from cg.api import CardType, all_attack, all_card_data

# Per-card feature vector layout (see CardDB.features):
#   [0:7]   cardType one-hot (POKEMON..SPECIAL_ENERGY)
#   [7]     hp / 300
#   [8]     retreatCost / 4
#   [9:21]  energyType one-hot (12 EnergyTypes)
#   [21:28] basic, stage1, stage2, ex, megaEx, tera, aceSpec
#   [28]    best attack damage / 300
#   [29]    number of attacks / 4
CARD_FEAT_DIM = 30
_N_ENERGY = 12


class CardDB:
    def __init__(self) -> None:
        self.cards = {c.cardId: c for c in all_card_data()}
        self.attacks = {a.attackId: a for a in all_attack()}
        self._feat_cache: dict[int, np.ndarray] = {}

    # --- raw lookups ---
    def card(self, card_id):
        return self.cards.get(card_id)

    def attack(self, attack_id):
        return self.attacks.get(attack_id)

    # --- scalar accessors (default to safe 0/None) ---
    def hp(self, card_id) -> int:
        c = self.cards.get(card_id)
        return c.hp if c else 0

    def attack_damage(self, attack_id) -> int:
        a = self.attacks.get(attack_id)
        return a.damage if a else 0

    # --- type predicates (cardType arrives as an int; IntEnum compares equal) ---
    def is_pokemon(self, card_id) -> bool:
        c = self.cards.get(card_id)
        return bool(c) and c.cardType == CardType.POKEMON

    def is_energy(self, card_id) -> bool:
        c = self.cards.get(card_id)
        return bool(c) and c.cardType in (CardType.BASIC_ENERGY, CardType.SPECIAL_ENERGY)

    def is_trainer(self, card_id) -> bool:
        c = self.cards.get(card_id)
        return bool(c) and c.cardType in (
            CardType.ITEM, CardType.TOOL, CardType.SUPPORTER, CardType.STADIUM,
        )

    def best_attack(self, card_id):
        """attackId of the highest-damage attack this card has, or None."""
        c = self.cards.get(card_id)
        if not c or not c.attacks:
            return None
        return max(c.attacks, key=self.attack_damage)

    def features(self, card_id) -> np.ndarray:
        """Fixed-size feature vector for a card id (zeros for None/unknown)."""
        cached = self._feat_cache.get(card_id)
        if cached is not None:
            return cached
        v = np.zeros(CARD_FEAT_DIM, dtype=np.float32)
        c = self.cards.get(card_id)
        if c is not None:
            ct = int(c.cardType)
            if 0 <= ct <= 6:
                v[ct] = 1.0
            v[7] = (c.hp or 0) / 300.0
            v[8] = (c.retreatCost or 0) / 4.0
            if c.energyType is not None and 0 <= int(c.energyType) < _N_ENERGY:
                v[9 + int(c.energyType)] = 1.0
            v[21] = float(bool(c.basic))
            v[22] = float(bool(c.stage1))
            v[23] = float(bool(c.stage2))
            v[24] = float(bool(c.ex))
            v[25] = float(bool(c.megaEx))
            v[26] = float(bool(c.tera))
            v[27] = float(bool(c.aceSpec))
            ba = self.best_attack(card_id)
            v[28] = (self.attack_damage(ba) if ba is not None else 0) / 300.0
            v[29] = len(c.attacks) / 4.0
        self._feat_cache[card_id] = v
        return v


_DB: CardDB | None = None


def get_card_db() -> CardDB:
    global _DB
    if _DB is None:
        _DB = CardDB()
    return _DB
