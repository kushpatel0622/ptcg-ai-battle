"""Numpy-free card/attack metadata lookup (vendored for the submission)."""
from cg.api import CardType, all_attack, all_card_data

class CardDB:
    def __init__(self):
        self.cards = {c.cardId: c for c in all_card_data()}
        self.attacks = {a.attackId: a for a in all_attack()}
    def card(self, cid): return self.cards.get(cid)
    def attack(self, aid): return self.attacks.get(aid)
    def hp(self, cid):
        c = self.cards.get(cid); return c.hp if c else 0
    def attack_damage(self, aid):
        a = self.attacks.get(aid); return a.damage if a else 0
    def is_pokemon(self, cid):
        c = self.cards.get(cid); return bool(c) and c.cardType == CardType.POKEMON
    def is_energy(self, cid):
        c = self.cards.get(cid); return bool(c) and c.cardType in (CardType.BASIC_ENERGY, CardType.SPECIAL_ENERGY)
    def is_trainer(self, cid):
        c = self.cards.get(cid); return bool(c) and c.cardType in (CardType.ITEM, CardType.TOOL, CardType.SUPPORTER, CardType.STADIUM)
    def best_attack(self, cid):
        c = self.cards.get(cid)
        if not c or not c.attacks: return None
        return max(c.attacks, key=self.attack_damage)

_DB = None
def get_card_db():
    global _DB
    if _DB is None:
        _DB = CardDB()
    return _DB
