"""Serialize a parsed Observation into compact text for an LLM prompt.

Keeps tokens low (cost control) while giving the model the board, both players'
visible state, the current decision, and a numbered list of legal options it
can pick by index.
"""
from __future__ import annotations

from cg.api import AreaType, EnergyType, OptionType, SelectContext

_ENERGY_LETTER = {
    EnergyType.COLORLESS: "C", EnergyType.GRASS: "G", EnergyType.FIRE: "R",
    EnergyType.WATER: "W", EnergyType.LIGHTNING: "L", EnergyType.PSYCHIC: "P",
    EnergyType.FIGHTING: "F", EnergyType.DARKNESS: "D", EnergyType.METAL: "M",
    EnergyType.DRAGON: "N", EnergyType.RAINBOW: "Y", EnergyType.TEAM_ROCKET: "T",
}

_CONTEXT_TEXT = {
    SelectContext.MAIN: "Choose your main action",
    SelectContext.SETUP_ACTIVE_POKEMON: "Choose your Active Pokémon for setup",
    SelectContext.SETUP_BENCH_POKEMON: "Choose a Basic Pokémon to put on your Bench",
    SelectContext.SWITCH: "Choose a Benched Pokémon to switch into the Active Spot",
    SelectContext.TO_ACTIVE: "Choose a Pokémon to make Active",
    SelectContext.TO_BENCH: "Choose a Pokémon to put on your Bench",
    SelectContext.TO_HAND: "Choose a card to put into your hand",
    SelectContext.DISCARD: "Choose a card to discard",
    SelectContext.ATTACK: "Choose an attack to use",
    SelectContext.EVOLVE: "Choose an evolution",
    SelectContext.DAMAGE: "Choose a Pokémon to damage",
    SelectContext.DAMAGE_COUNTER: "Choose a Pokémon to place damage counters on",
    SelectContext.HEAL: "Choose a Pokémon to heal",
    SelectContext.IS_FIRST: "Decide whether to go first",
    SelectContext.MULLIGAN: "Decide whether to take the extra draw",
    SelectContext.ACTIVATE: "Decide whether to activate the effect",
    SelectContext.COIN_HEAD: "Choose heads or tails",
}


def card_name(db, card_id) -> str:
    if card_id is None:
        return "facedown card"
    c = db.card(card_id)
    return c.name if c else f"card#{card_id}"


def _energy_str(pkmn) -> str:
    if not pkmn.energies:
        return ""
    letters = "".join(_ENERGY_LETTER.get(EnergyType(e), "?") for e in pkmn.energies)
    return f" [{letters}]"


def _pkmn_str(pkmn, db) -> str:
    if pkmn is None:
        return "none"
    tools = f" +{len(pkmn.tools)}tool" if pkmn.tools else ""
    return f"{card_name(db, pkmn.id)} (HP {pkmn.hp}/{pkmn.maxHp}){_energy_str(pkmn)}{tools}"


def _active(p):
    return p.active[0] if p.active and len(p.active) > 0 else None


def _conditions(p) -> str:
    flags = [n for n, v in (("Poisoned", p.poisoned), ("Burned", p.burned),
             ("Asleep", p.asleep), ("Paralyzed", p.paralyzed), ("Confused", p.confused)) if v]
    return ", ".join(flags)


def _resolve_card_name(obs, opt, db) -> str:
    """Name the card an option references, resolving hand/discard index when the
    option has no cardId (e.g. play/attach/evolve from hand)."""
    if opt.cardId is not None:
        return card_name(db, opt.cardId)
    yi = obs.current.yourIndex
    try:
        p = obs.current.players[yi]
        if opt.area == AreaType.HAND and opt.index is not None and p.hand and opt.index < len(p.hand):
            return card_name(db, p.hand[opt.index].id)
        if opt.area == AreaType.DISCARD and opt.index is not None and opt.index < len(p.discard):
            return card_name(db, p.discard[opt.index].id)
    except Exception:
        pass
    return "a card"


def describe_state(obs, db) -> str:
    st = obs.current
    yi = st.yourIndex
    me, opp = st.players[yi], st.players[1 - yi]
    lines = [f"Turn {st.turn} - your turn (you are player {yi})."]

    my_bench = "; ".join(_pkmn_str(b, db) for b in me.bench) or "empty"
    my_hand = ", ".join(card_name(db, c.id) for c in (me.hand or [])) or "(unknown)"
    lines.append(f"YOU  Active: {_pkmn_str(_active(me), db)}")
    lines.append(f"     Bench: {my_bench}")
    lines.append(f"     Hand({me.handCount}): {my_hand}")
    lines.append(f"     Prizes left: {len(me.prize)} | Deck: {me.deckCount} | Discard: {len(me.discard)}")

    opp_bench = "; ".join(_pkmn_str(b, db) for b in opp.bench) or "empty"
    lines.append(f"OPP  Active: {_pkmn_str(_active(opp), db)}")
    lines.append(f"     Bench: {opp_bench}")
    lines.append(f"     Hand: {opp.handCount} | Prizes left: {len(opp.prize)} | Deck: {opp.deckCount}")

    cond_bits = []
    if _conditions(me):
        cond_bits.append(f"your active: {_conditions(me)}")
    if _conditions(opp):
        cond_bits.append(f"opp active: {_conditions(opp)}")
    if cond_bits:
        lines.append("Conditions: " + "; ".join(cond_bits))
    return "\n".join(lines)


def _inplay_name(obs, opt, db) -> str:
    yi = obs.current.yourIndex
    pi = opt.playerIndex if opt.playerIndex is not None else yi
    try:
        p = obs.current.players[pi]
        if opt.inPlayArea == AreaType.ACTIVE:
            a = _active(p)
            return card_name(db, a.id) if a else "Active"
        if opt.inPlayArea == AreaType.BENCH and opt.inPlayIndex is not None and opt.inPlayIndex < len(p.bench):
            return card_name(db, p.bench[opt.inPlayIndex].id)
    except Exception:
        pass
    return "a Pokémon"


def describe_option(opt, db, obs) -> str:
    t = opt.type
    name = _resolve_card_name(obs, opt, db)
    if t == OptionType.NUMBER:
        return str(opt.number)
    if t == OptionType.YES:
        return "Yes"
    if t == OptionType.NO:
        return "No"
    if t == OptionType.PLAY:
        return f"Play {name} from hand"
    if t == OptionType.ATTACH:
        return f"Attach {name} to {_inplay_name(obs, opt, db)}"
    if t == OptionType.EVOLVE:
        return f"Evolve into {name}"
    if t == OptionType.ABILITY:
        return f"Use ability of {name}"
    if t == OptionType.DISCARD:
        return f"Discard {name}"
    if t == OptionType.RETREAT:
        return "Retreat the Active Pokémon"
    if t == OptionType.ATTACK:
        atk = db.attack(opt.attackId)
        if atk:
            return f"Attack: {atk.name} ({atk.damage} dmg)"
        return "Attack"
    if t == OptionType.END:
        return "End turn"
    if t == OptionType.SKILL:
        return f"Resolve skill of {name}"
    if t == OptionType.ENERGY:
        return f"Energy {name}" + (f" x{opt.count}" if opt.count else "")
    if t in (OptionType.ENERGY_CARD, OptionType.TOOL_CARD):
        return f"{name}"
    if t == OptionType.CARD:
        return name
    if t == OptionType.SPECIAL_CONDITION:
        return f"Special condition {opt.specialConditionType}"
    return name


def build_user_prompt(obs, db) -> str:
    sel = obs.select
    ctx = _CONTEXT_TEXT.get(sel.context, f"Make a selection ({SelectContext(sel.context).name})")
    if sel.minCount == sel.maxCount:
        count_txt = f"exactly {sel.maxCount} option(s)"
    else:
        count_txt = f"between {sel.minCount} and {sel.maxCount} option(s)"
    opt_lines = "\n".join(f"  {i}: {describe_option(o, db, obs)}" for i, o in enumerate(sel.option))
    return (
        f"{describe_state(obs, db)}\n\n"
        f"DECISION: {ctx}. Choose {count_txt}.\n"
        f"Options:\n{opt_lines}\n\n"
        f'Reply with JSON only: {{"choice": [option numbers], "reason": "short"}}'
    )
