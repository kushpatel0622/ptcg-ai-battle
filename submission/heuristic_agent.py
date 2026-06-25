"""Rule-based heuristic agent.

Goal: a deterministic, sensible player that crushes the random baseline and
serves as an RL opponent / sanity benchmark. It does NOT try to be optimal.

Strategy summary:
  - MAIN turn: develop board and attach energy before attacking; attacking ends
    the turn, so it is chosen only after cheaper value plays are exhausted.
  - ATTACK: pick the highest-damage attack (also correct for "disable opponent
    attack", where neutralising their biggest attack is best).
  - Setup / switch / promote: pick the highest-HP Pokémon.
  - Yes/No: context-aware defaults (go first, take draws, activate effects).
  - Counts: pick the largest number (draw/damage/heal "more is better").
  - Card picks: for cards we GAIN, take the most valuable up to maxCount; for
    cards we LOSE (discard/return), give up the fewest, least valuable; for
    OFFENSE (placing damage), target the opponent's Pokémon.

The engine only ever offers legal options, so we just choose among them and a
final sanitize step guarantees the [minCount, maxCount]/uniqueness contract.
"""
from __future__ import annotations

from cg.api import (
    AreaType,
    OptionType,
    SelectContext,
    SelectType,
    to_observation_class,
)

from cards import get_card_db
from deck_io import default_deck

# --- MAIN action priority (higher = do first). Attacking ends the turn, so it
#     sits below board development; ABILITY is below ATTACK to avoid rare
#     repeatable-ability loops while still attacking every turn. ---
_MAIN_PRIORITY = {
    OptionType.EVOLVE: 6,
    OptionType.ATTACH: 5,
    OptionType.PLAY: 4,
    OptionType.ATTACK: 3,
    OptionType.ABILITY: 2,
    OptionType.RETREAT: 1,
    OptionType.END: 0,
    OptionType.DISCARD: -1,
}

_GAIN_CTX = {
    SelectContext.SETUP_ACTIVE_POKEMON, SelectContext.SETUP_BENCH_POKEMON,
    SelectContext.TO_ACTIVE, SelectContext.TO_BENCH, SelectContext.TO_FIELD,
    SelectContext.TO_HAND, SelectContext.HEAL, SelectContext.REMOVE_DAMAGE_COUNTER,
    SelectContext.EVOLVES_FROM, SelectContext.EVOLVES_TO, SelectContext.ATTACH_FROM,
    SelectContext.ATTACH_TO, SelectContext.LOOK, SelectContext.EFFECT_TARGET,
    SelectContext.SWITCH,
}
_LOSE_CTX = {
    SelectContext.DISCARD, SelectContext.TO_DECK, SelectContext.TO_DECK_BOTTOM,
    SelectContext.NOT_MOVE, SelectContext.DEVOLVE, SelectContext.DISCARD_ENERGY_CARD,
    SelectContext.DISCARD_TOOL_CARD, SelectContext.SWITCH_ENERGY_CARD,
    SelectContext.DISCARD_CARD_OR_ATTACHED_CARD, SelectContext.DISCARD_ENERGY,
    SelectContext.TO_HAND_ENERGY, SelectContext.TO_DECK_ENERGY,
    SelectContext.SWITCH_ENERGY, SelectContext.DETACH_FROM,
}
_OFFENSE_CTX = {
    SelectContext.DAMAGE, SelectContext.DAMAGE_COUNTER, SelectContext.DAMAGE_COUNTER_ANY,
}


def _card_value(opt, db) -> float:
    """Rough importance of the card an option references (higher = keep)."""
    cid = opt.cardId
    if cid is None:
        return 0.0
    if db.is_pokemon(cid):
        c = db.card(cid)
        v = 100.0 + db.hp(cid)
        if c and (c.ex or c.megaEx):
            v += 60.0
        return v
    if db.is_trainer(cid):
        return 40.0
    if db.is_energy(cid):
        return 10.0
    return 5.0


def _choose_main(sel, db) -> int:
    best_i, best_key = 0, None
    for i, opt in enumerate(sel.option):
        pri = _MAIN_PRIORITY.get(opt.type, 0)
        sub = 0
        if opt.type == OptionType.ATTACK and opt.attackId is not None:
            sub = db.attack_damage(opt.attackId)
        elif opt.type == OptionType.ATTACH and opt.inPlayArea == AreaType.ACTIVE:
            sub = 1  # prefer attaching energy to the active attacker
        key = (pri, sub)
        if best_key is None or key > best_key:
            best_key, best_i = key, i
    return best_i


def _best_attack(sel, db) -> int:
    best_i, best_d = 0, -1
    for i, opt in enumerate(sel.option):
        d = db.attack_damage(opt.attackId) if opt.attackId is not None else 0
        if d > best_d:
            best_d, best_i = d, i
    return best_i


def _yes_no(sel) -> int:
    yes = next((i for i, o in enumerate(sel.option) if o.type == OptionType.YES), None)
    no = next((i for i, o in enumerate(sel.option) if o.type == OptionType.NO), None)
    # Default to YES for: go first, take mulligan draws, win the coin, activate
    # effects, pick the first effect, devolve more. Fall back to index 0.
    want_yes = True
    return (yes if want_yes else no) if (yes is not None or no is not None) else 0


def _max_number(sel) -> int:
    best_i, best_v = 0, None
    for i, o in enumerate(sel.option):
        v = o.number if o.number is not None else 0
        if best_v is None or v > best_v:
            best_v, best_i = v, i
    return best_i


def _choose_cards(sel, obs, db) -> list[int]:
    n = len(sel.option)
    lo, hi = max(0, sel.minCount), min(sel.maxCount, n)
    ctx = sel.context
    if ctx in _OFFENSE_CTX:
        yi = obs.current.yourIndex if obs.current is not None else 0
        opp = [i for i, o in enumerate(sel.option)
               if o.playerIndex is not None and o.playerIndex != yi]
        pool = opp if opp else list(range(n))
        return pool[:hi] if hi > 0 else []
    by_value = sorted(range(n), key=lambda i: _card_value(sel.option[i], db))
    if ctx in _LOSE_CTX:
        return by_value[:lo]  # give up the fewest, least valuable
    if ctx in _GAIN_CTX:
        return list(reversed(by_value))[:hi]  # take the most valuable, up to max
    return by_value[:lo] if lo > 0 else []  # neutral: do the minimum


def _sanitize(chosen, sel) -> list[int]:
    n = len(sel.option)
    out: list[int] = []
    for i in chosen:
        if 0 <= i < n and i not in out:
            out.append(i)
    out = out[: sel.maxCount]
    if len(out) < sel.minCount:
        for i in range(n):
            if i not in out:
                out.append(i)
                if len(out) >= sel.minCount:
                    break
    return out


def _choose(sel, obs, db) -> list[int]:
    if len(sel.option) == 0:
        return []
    st = sel.type
    if st == SelectType.MAIN:
        return [_choose_main(sel, db)]
    if st == SelectType.ATTACK:
        return [_best_attack(sel, db)]
    if st == SelectType.YES_NO:
        return [_yes_no(sel)]
    if st == SelectType.COUNT:
        return [_max_number(sel)]
    if st == SelectType.EVOLVE:
        return [0]
    if st == SelectType.SKILL:
        return list(range(min(sel.maxCount, len(sel.option))))
    # CARD / ATTACHED_CARD / CARD_OR_ATTACHED_CARD / ENERGY
    return _choose_cards(sel, obs, db)


def heuristic_agent(obs_dict: dict) -> list[int]:
    obs = to_observation_class(obs_dict)
    if obs.select is None:  # deck selection (kaggle_environments path)
        return default_deck()
    db = get_card_db()
    return _sanitize(_choose(obs.select, obs, db), obs.select)
