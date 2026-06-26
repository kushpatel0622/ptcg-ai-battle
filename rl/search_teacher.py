"""SearchTeacher: a forward-search agent built on the engine's lookahead.

Same interface as ``baselines.heuristic_agent.heuristic_agent``
(``callable(obs_dict) -> list[int]``), so it can pilot a deck in
``engine.harness.play_match`` and serve as a stronger teacher for behavior
cloning. It is also deployable as the submission agent (needs only ``cg``).

Strategy
--------
For the *strategic single-choice* decisions (exactly one of N>1 options:
``sel.minCount == 1 and sel.maxCount == 1 and n > 1``) the teacher forks the sim
at the current decision and rolls each option forward, scoring the result:

  1. Determinize hidden info (fill our own deck/prizes from the known 60-card
     deck list minus everything visible; fill the opponent with generic Basic +
     Energy filler, or — with ``opp_model`` — from a real archetype list).
  2. ``search_begin(...)`` to fork, then for each option ``i`` roll it forward
     with the heuristic to the horizon and score from *our* perspective.
  3. Keep the heuristic's pick as a prior; override only when an option beats it
     by ``override_margin``.

Tunable knobs (all default to the original fast 1-ply behaviour):
  * ``plies``      — 1 = roll to the end of my turn; 2 = also roll the opponent's
                     reply and score at the start of my next turn.
  * ``opp_model``  — deal the opponent's hidden cards from a real meta deck so a
                     2-ply rollout faces a realistic attacker (the lever that
                     actually helped: ~+5% vs the heuristic; see TRAINING_LOG R3.3).
  * ``samples``    — average each option over N determinizations (measured to add
                     ~nothing over 1; kept for completeness).
  * ``time_budget``— optional per-move wall-clock cap (heuristic fallback under
                     pressure) for the grader's per-move limit.

Everything else (multi-select, forced, optional, deck selection) is delegated to
the hand-coded heuristic. Any search error falls back to the heuristic for that
decision, so games always finish and we never leak search memory.

Eval (higher == better, from ``yourIndex``'s perspective) — see ``_evaluate``:
    + W_PRIZE * (prizes taken − prizes given up)   # win condition, dominates
    + W_DMG   * (damage dealt to the opponent)
    + W_HP    * (sum of my Pokémon hp; at 2-ply this is my hp AFTER the
                 opponent's reply, i.e. the defensive signal)
    ± WIN_BONUS on a decided game.
"""
from __future__ import annotations

import random
from time import perf_counter

from cg.api import to_observation_class
from cg.api import search_begin, search_step, search_end

from baselines.heuristic_agent import heuristic_agent, _choose as _heur_choose, _sanitize as _heur_sanitize
from engine.cards import get_card_db
from engine.decks import default_deck

# --- Generic opponent filler (both valid per the API docs) ---
_STARYU_ID = 1030      # a Basic Pokémon
_BASIC_W_ENERGY = 3    # Basic {W} Energy

# --- Eval weights (scores are deltas vs the root state; see _evaluate). Prizes
#     dominate: one prize (1000) outweighs any realistic damage/board term. ---
W_PRIZE = 1000.0     # per prize taken / given up (win condition)
W_DMG = 2.0          # per HP of damage dealt to the opponent this decision
W_HP = 1.0           # per HP of our own board kept healthy / developed
WIN_BONUS = 1_000_000.0

# Search only overrides the heuristic's choice when a different option's
# rollout-to-end-of-turn score beats the heuristic option's score by at least
# this margin. Keeps the heuristic's strong move-ordering as the prior and only
# deviates on high-confidence improvements (a prize swing dwarfs this).
OVERRIDE_MARGIN = 20.0
# Max selections to roll forward inside a forked turn before giving up.
ROLLOUT_DEPTH = 60
# 2-ply rollouts span my turn + the opponent's full turn, so they need a deeper
# step budget (a busy two-turn span is ~10-25 selections; cap generously).
ROLLOUT_DEPTH_2PLY = 140


def _pokemon_hp_sum(pstate) -> int:
    total = 0
    for a in (pstate.active or []):
        if a is not None:
            total += a.hp or 0
    for b in (pstate.bench or []):
        if b is not None:
            total += b.hp or 0
    return total


def _collect_known_ids(pstate) -> list[int]:
    """Every card id visible among a player's in-play Pokémon (+ attachments,
    pre-evolutions) and discard pile."""
    ids: list[int] = []

    def add_pokemon(p):
        if p is None:
            return
        ids.append(p.id)
        for c in (p.energyCards or []):
            ids.append(c.id)
        for c in (p.tools or []):
            ids.append(c.id)
        for c in (p.preEvolution or []):
            ids.append(c.id)

    for a in (pstate.active or []):
        add_pokemon(a)
    for b in (pstate.bench or []):
        add_pokemon(b)
    for c in (pstate.discard or []):
        ids.append(c.id)
    return ids


# --- Dynamic-damage attacks. Some attacks read damage=0 in the card DB because
#     their damage is computed at resolution time (e.g. "50 per card in the
#     opponent's hand"). The heuristic ranks attacks by db.attack_damage, so it
#     NEVER picks these — a one-sided mistake the heuristic opponent makes every
#     game. We correct the ATTACK ranking with the true damage so the agent (and
#     its simulated opponent in the rollout) uses the genuinely strongest attack.
def _opp_ex_count(opp) -> int:
    n = 0
    for p in list(opp.active or []) + list(opp.bench or []):
        if p is None:
            continue
        c = get_card_db().card(p.id)
        if c and (getattr(c, "ex", False) or getattr(c, "megaEx", False)):
            n += 1
    return n


def _self_damage_counters(me) -> int:
    a = (me.active or [None])[0]
    if a is None:
        return 0
    maxhp = get_card_db().hp(a.id) or 0
    return max(0, (maxhp - (a.hp or 0))) // 10


def _attack_damage_dyn(opt, obs, db) -> int:
    """True damage of an attack option, correcting the attacks whose DB damage is
    0 because the engine computes it at resolution time. The heuristic ranks by
    db.attack_damage=0 and so never plays these — a one-sided, every-game mistake.
    Covers the dynamic-damage attacks across our 8 decks (utility 0-dmg attacks
    like Call for Family stay 0)."""
    aid = getattr(opt, "attackId", None)
    if aid is None:
        return 0
    st = obs.current
    try:
        if st is not None:
            yi = st.yourIndex
            opp = st.players[1 - yi]
            me = st.players[yi]
            if aid == 1240:    # Resentful Refrain: 50 x cards in opp's hand
                return 50 * (opp.handCount or 0)
            if aid == 183:     # Cruel Arrow: 100 to 1 of opp's Pokémon (free snipe)
                return 100
            if aid == 252:     # Sonic Peridot: 100 to each opp ex/V
                return 100 * max(1, _opp_ex_count(opp))
            if aid == 184:     # Irritated Outburst: 60 x prizes opp has taken
                return 60 * (6 - len(opp.prize))
            if aid == 420:     # Powerful Rage: 20 x damage counters on self
                return 20 * _self_damage_counters(me)
    except Exception:
        pass
    return db.attack_damage(aid)


def _choose_dyn(sel, obs, db):
    """Heuristic move choice, but ATTACK options are ranked by TRUE (dynamic)
    damage so dynamic-damage attacks (Resentful Refrain) aren't invisible."""
    from cg.api import SelectType
    if sel.type == SelectType.ATTACK and len(sel.option) > 0:
        best_i, best_d = 0, -1
        for i, o in enumerate(sel.option):
            d = _attack_damage_dyn(o, obs, db)
            if d > best_d:
                best_d, best_i = d, i
        return [best_i]
    return _heur_choose(sel, obs, db)


# Attacks that DON'T hit the opponent's active (chosen target / spread), so their
# damage must not be compared to the active's HP in the lethal-KO shortcut.
_SPREAD_ATTACKS = {183, 252}   # Cruel Arrow (snipe), Sonic Peridot (each ex)


def _improved_pick(sel, obs, db, bench_when_thin):
    """Core of the improved rollout pilot (MAIN only); returns an option-index list
    or None to defer to the dynamic heuristic. See docs/strategies/S7-rollout-pilot.md.
      1. LETHAL KO: if an ATTACK that hits the active has true damage >= the opp
         active's HP, take it now -- banks the KO without overcommitting the hand
         (smaller hand => less Resentful Refrain taken next turn). Spread/snipe
         attacks (don't hit the active) are excluded from this shortcut.
      2. BENCH-WHEN-THIN (only if bench_when_thin): if our bench is empty, play a
         Basic to the bench first. Resolved via the option's HAND INDEX (PLAY options
         carry `index`, not `cardId`)."""
    from cg.api import SelectType, OptionType
    if sel.type != SelectType.MAIN or obs.current is None:
        return None
    st = obs.current
    yi = st.yourIndex
    me = st.players[yi]
    opp = st.players[1 - yi]
    oa = (opp.active or [None])
    opp_hp = oa[0].hp if (oa and oa[0]) else None
    hand = me.hand or []
    best_atk_i, best_atk_d, bench_play_i = None, -1, None
    for i, o in enumerate(sel.option):
        if (o.type == OptionType.ATTACK and o.attackId is not None
                and o.attackId not in _SPREAD_ATTACKS):
            d = _attack_damage_dyn(o, obs, db)
            if d > best_atk_d:
                best_atk_d, best_atk_i = d, i
        elif (bench_when_thin and bench_play_i is None and o.type == OptionType.PLAY
              and o.index is not None and 0 <= o.index < len(hand)):
            cid = hand[o.index].id
            if db.is_pokemon(cid) and getattr(db.card(cid), "basic", False):
                bench_play_i = i
    if (best_atk_i is not None and opp_hp is not None
            and best_atk_d > 0 and best_atk_d >= opp_hp):
        return [best_atk_i]
    if bench_when_thin and bench_play_i is not None:
        my_bench = len([b for b in (me.bench or []) if b is not None])
        if my_bench < 1:
            return [bench_play_i]
    return None


def _choose_improved(sel, obs, db):
    """Improved pilot, lethal-KO only (the as-measured, shipped behaviour)."""
    pick = _improved_pick(sel, obs, db, bench_when_thin=False)
    return pick if pick is not None else _choose_dyn(sel, obs, db)


def _choose_improved_bench(sel, obs, db):
    """Improved pilot + a WORKING bench-when-thin rule (experiment)."""
    pick = _improved_pick(sel, obs, db, bench_when_thin=True)
    return pick if pick is not None else _choose_dyn(sel, obs, db)


class SearchTeacher:
    def __init__(self, deck=None, rng=None, plies=1, opp_model=None, samples=1,
                 override_margin=None, time_budget=None,
                 w_prize=None, w_dmg=None, w_hp=None,
                 value_net=None, v_scale=0.0, dynamic_attack=True,
                 w_bench=0.0, fragile_penalty=0.0, bench_target=3,
                 w_handpen=0.0, rollout_policy="heuristic"):
        """deck: our full 60-card deck (list of card ids). Used to determinize
        our own hidden cards. Falls back to ``default_deck()`` if omitted.

        plies: rollout horizon.
          1 = roll each option to the end of MY turn and score there (the legacy
              behaviour: fast, but blind to the opponent's reply).
          2 = additionally roll the opponent's full turn (heuristic-piloted on
              the determinized board) and score at the start of MY NEXT turn, so
              the eval sees the opponent's response — e.g. a return KO that takes
              a prize back. Defends against plays that win tempo but hang an
              attacker. Costs ~2-3x the rollout steps per option.

        opp_model: optional 60-card list standing in for the opponent's deck. The
          opponent's HIDDEN cards (deck / hand / prizes) are dealt from it instead
          of generic Basic + Energy filler, so a 2-ply rollout simulates a real
          attacker setting up and threatening KOs rather than a passive blob. Set
          this to the dominant ladder archetype (e.g. Mega Starmie ex). Ignored
          for 1-ply (the opponent's turn is never simulated there). The opponent's
          *visible* board always comes from the real observation regardless."""
        self.deck = list(deck) if deck else list(default_deck())
        self.rng = rng or random.Random(0)
        # plies = rollout horizon in half-turns past the current decision. 1 = end
        # of my turn (legacy); 2 = after the opponent's reply; 3+ = deeper (my
        # turn -> opp -> my turn ...). The large per-game time budget (~600s)
        # leaves ample room to go past 2 (see docs/REPORT.md S3).
        self.plies = max(1, int(plies)) if plies else 1
        self.rollout_depth = ROLLOUT_DEPTH if self.plies == 1 else 40 + 70 * self.plies
        # The opponent model / multi-sample only matter once the opponent's turn is
        # simulated (plies>=2); keep them off at 1-ply to preserve behaviour.
        self.opp_model = list(opp_model) if (opp_model and self.plies >= 2) else None
        # ISMCTS-lite: average each option's score over this many independent
        # determinizations to denoise the opponent's random draws (the variance a
        # single 2-ply rollout suffers most). Only worth >1 at 2-ply; 1 keeps the
        # legacy single-rollout behaviour exactly.
        self.samples = max(1, int(samples)) if self.plies >= 2 else 1
        # Margin by which an option's rollout score must beat the heuristic's pick
        # before we override it. The heuristic prior is strong, so the bar guards
        # against overriding on noise. At 2-ply the score carries a prize-scale
        # (±W_PRIZE) opponent-reply term whose determinization variance dwarfs the
        # default HP-scale margin (20), so a 2-ply agent usually wants a much
        # larger margin (e.g. ~W_PRIZE) to avoid chasing phantom return-KOs.
        self.override_margin = OVERRIDE_MARGIN if override_margin is None else float(override_margin)
        # Optional per-decision wall-clock budget (seconds). None = unlimited
        # (used for offline measurement). When set, the sampling loop stops once
        # the budget is spent — AFTER at least one full sample (so every option is
        # scored once and the comparison stays fair). A safety valve for the
        # grader's per-move time limit; samples=3 peaked at ~1.5 s/move, so a
        # budget like 0.8 caps the tail toward a single ~0.5 s sample.
        self.time_budget = time_budget
        # Eval weights (default to the module constants). Exposed for tuning; see
        # _evaluate. Only the RATIOS w_dmg/w_prize and w_hp/w_prize (and the
        # margin relative to them) matter for option ranking.
        self.w_prize = W_PRIZE if w_prize is None else float(w_prize)
        self.w_dmg = W_DMG if w_dmg is None else float(w_dmg)
        self.w_hp = W_HP if w_hp is None else float(w_hp)
        # Optional learned leaf evaluator (AlphaZero-style). `value_net` is a
        # callable: state_vec[float32, STATE_DIM] -> scalar in [0,1] = P(the
        # to-move player wins). Used ONLY at a my-perspective leaf (the 2-ply
        # horizon = start of my next turn), added as `v_scale * V`. Keeps the
        # exact prize/win terms; typically paired with w_dmg=w_hp=0 so V replaces
        # the crude hp-sum board proxy. None -> no torch/numpy import (clean).
        self.value_net = value_net
        self.v_scale = float(v_scale)
        # Rank ATTACK options by true (dynamic) damage so the agent and its
        # rollout opponent use Resentful Refrain etc. (the heuristic can't see
        # them). Strictly more correct; on by default.
        self.dynamic_attack = dynamic_attack
        # --- Robustness terms (default 0 => baseline behaviour unchanged). Added
        # after replay 81844919 showed the agent routinely plays a lone/thin board
        # (15% never bench, 42% <=1 Pokemon in play) and holds fat hands that feed
        # the mirror's Resentful Refrain (50 x opp hand). See docs/REPORT.md S1/S2.
        # w_bench: reward per benched Pokemon (capped at bench_target) -> develop.
        # fragile_penalty: penalty when <=1 Pokemon in play at the leaf (one KO
        #   from losing -> "no active Pokemon" loss). Read AFTER the opp reply at
        #   2-ply, so it directly values surviving on board.
        # w_handpen: penalty per card in my hand when an opponent attacker in play
        #   can use Resentful Refrain (attack 1240), discouraging fat hands.
        self.w_bench = float(w_bench)
        self.fragile_penalty = float(fragile_penalty)
        self.bench_target = int(bench_target)
        self.w_handpen = float(w_handpen)
        # Rollout pilot: "heuristic" (default) or "improved" (lethal-KO + bench-when-
        # thin; see _choose_improved). The pilot drives BOTH the rollout simulation
        # (mine + the opponent's turn at 2-ply) AND the search's prior/fallback, so a
        # better pilot sharpens option values. Deployable (pure function, no deps).
        self.rollout_policy = rollout_policy

    def _pilot_choose(self, sel, obs, db):
        """Move choice used as the search prior and the rollout pilot."""
        if self.rollout_policy == "improved":
            return _choose_improved(sel, obs, db)
        if self.rollout_policy == "improved_bench":
            return _choose_improved_bench(sel, obs, db)
        return _choose_dyn(sel, obs, db) if self.dynamic_attack else _heur_choose(sel, obs, db)

    # ---- helpers -------------------------------------------------------

    def _learnable(self, sel, n) -> bool:
        # Exactly one of N>1 options: a clean strategic choice worth searching.
        return sel.minCount == 1 and sel.maxCount == 1 and n > 1

    def _determinize(self, obs):
        """Return (your_deck, your_prize, opp_deck, opp_prize, opp_hand,
        opp_active) satisfying the search_begin length/content requirements."""
        state = obs.current
        yi = state.yourIndex
        me = state.players[yi]
        opp = state.players[1 - yi]

        # Known of OUR cards = hand + everything in play + discard.
        known: list[int] = []
        if me.hand:
            known += [c.id for c in me.hand]
        known += _collect_known_ids(me)

        # Unknown remainder = full deck minus known (multiset subtraction).
        remainder = list(self.deck)
        for cid in known:
            if cid in remainder:
                remainder.remove(cid)
        self.rng.shuffle(remainder)

        deck_n = me.deckCount
        prize_n = len(me.prize)
        your_deck = remainder[:deck_n]
        your_prize = remainder[deck_n:deck_n + prize_n]
        # Pad defensively if our deck list under-counts (shouldn't normally).
        while len(your_deck) < deck_n:
            your_deck.append(_BASIC_W_ENERGY)
        while len(your_prize) < prize_n:
            your_prize.append(_BASIC_W_ENERGY)

        # Opponent hidden cards. With an opp_model (2-ply only) deal their deck /
        # hand / prizes from a real archetype so the simulated opponent turn can
        # set up and attack; otherwise use generic Basic + Energy filler.
        if self.opp_model:
            opp_deck, opp_hand, opp_prize = self._fill_opponent_from_model(opp)
        else:
            filler = [_STARYU_ID, _BASIC_W_ENERGY]

            def fill(k):
                if k <= 0:
                    return []
                out = (filler * (k // 2 + 1))[:k]
                if _STARYU_ID not in out:
                    out[0] = _STARYU_ID
                return out

            opp_deck = fill(opp.deckCount) or [_STARYU_ID]
            opp_hand = (filler * (opp.handCount // 2 + 1))[:opp.handCount]
            opp_prize = (filler * (len(opp.prize) // 2 + 1))[:len(opp.prize)]

        opp_active: list[int] = []
        oa = opp.active or []
        if len(oa) > 0 and oa[0] is None:
            opp_active = [_STARYU_ID]

        return your_deck, your_prize, opp_deck, opp_prize, opp_hand, opp_active

    def _fill_opponent_from_model(self, opp):
        """Deal the opponent's hidden deck/hand/prizes from ``self.opp_model``,
        minus the opponent's visible cards (so we don't duplicate what's already
        in play). Guarantees >=1 Basic Pokémon in the deck (search_begin requires
        one at setup). Pads with Basic Energy if the model is short."""
        db = get_card_db()
        pool = list(self.opp_model)
        for cid in _collect_known_ids(opp):
            if cid in pool:
                pool.remove(cid)
        self.rng.shuffle(pool)

        deck_n, hand_n, prize_n = opp.deckCount, opp.handCount, len(opp.prize)
        need = deck_n + hand_n + prize_n
        while len(pool) < need:
            pool.append(_BASIC_W_ENERGY)

        opp_deck = pool[:deck_n]
        opp_hand = pool[deck_n:deck_n + hand_n]
        opp_prize = pool[deck_n + hand_n:need]

        def is_basic_pokemon(cid):
            c = db.card(cid)
            return bool(c) and db.is_pokemon(cid) and bool(getattr(c, "basic", False))

        if deck_n > 0 and not any(is_basic_pokemon(c) for c in opp_deck):
            basic = next((c for c in self.opp_model if is_basic_pokemon(c)), _STARYU_ID)
            opp_deck[0] = basic
        return opp_deck, opp_hand, opp_prize

    def _evaluate(self, search_obs, yi, baseline) -> float:
        """Score a forked state from player ``yi``'s perspective; higher better.

        Scored as the *change* relative to ``baseline`` (the root state captured
        at decision time): prizes taken, damage dealt to the opponent, and our
        own board HP preserved. Delta-scoring is essential because the opponent's
        deck is determinized with generic filler, so the opponent's *absolute*
        board HP is meaningless noise; only the damage we inflict (a reduction
        from baseline) and our own real board are trustworthy signals.

        At 2-ply this state is the start of MY NEXT TURN, i.e. AFTER the opponent
        replied, and *every* term is read here ON PURPOSE. Measuring my own board
        HP after the opponent's turn is the whole point of going deeper: it is the
        defensive signal — an option that leaves me healthier after the opponent's
        chip damage / return attack scores higher. (An earlier "fix" that
        re-baselined the board terms to the end of MY turn was measured to be
        ~5-6 pts WORSE vs the heuristic on every seed, because it discarded
        exactly this signal; see docs/TRAINING_LOG.md R3.3. The damage-dealt term
        merely fading toward 0 after the opponent re-develops is harmless — it is
        a tiny W_DMG=2 tie-breaker — whereas the post-opponent board HP is the
        load-bearing 2-ply signal.)"""
        cur = search_obs.current
        if cur is None:
            return 0.0
        me = cur.players[yi]
        opp = cur.players[1 - yi]

        score = 0.0
        # Prizes taken (6 - remaining) vs given up. The win condition is taking
        # all 6 prizes, so this dominates everything else.
        my_taken = 6 - len(me.prize)
        opp_taken = 6 - len(opp.prize)
        score += self.w_prize * (my_taken - opp_taken)

        # Damage dealt to the opponent this decision = reduction of their board
        # HP from the baseline. Rewards attacking / chip damage. Clamp at 0 so a
        # (fake) opponent gaining HP via its filler deck can't punish us.
        opp_hp_now = _pokemon_hp_sum(opp)
        dmg_dealt = max(0, baseline["opp_hp"] - opp_hp_now)
        score += self.w_dmg * dmg_dealt

        # Our own board strength. At 1-ply this rewards developing/keeping
        # attackers healthy; at 2-ply it doubles as the defensive signal (my HP
        # after the opponent's reply). Real info either way.
        score += self.w_hp * _pokemon_hp_sum(me)

        # --- Robustness terms (S1/S2; 0 by default). ---
        if self.w_bench or self.fragile_penalty or self.w_handpen:
            my_bench = len([b for b in (me.bench or []) if b is not None])
            my_active = len([a for a in (me.active or []) if a is not None])
            my_inplay = my_active + my_bench
            # S1: reward developing a bench (diminishing past bench_target).
            if self.w_bench:
                score += self.w_bench * min(my_bench, self.bench_target)
            # S1: being at <=1 Pokemon in play is one KO from a board-out loss.
            # Only penalise in a live (non-terminal) state; a real loss already
            # carries -WIN_BONUS below.
            if self.fragile_penalty and cur.result == -1 and my_inplay <= 1:
                score -= self.fragile_penalty
            # S2: a fat hand facing a Resentful-Refrain attacker (attack 1240) is a
            # liability (it does 50 x my hand). Penalise hand size when the opp has
            # such an attacker in play at this leaf.
            if self.w_handpen and (me.hand is not None or True):
                db = get_card_db()
                opp_can_refrain = False
                for p in list(opp.active or []) + list(opp.bench or []):
                    if p is None:
                        continue
                    c = db.card(p.id)
                    if c and 1240 in (getattr(c, "attacks", None) or []):
                        opp_can_refrain = True
                        break
                if opp_can_refrain:
                    my_hand = me.handCount or 0
                    score -= self.w_handpen * my_hand

        # Learned positional eval (optional, AlphaZero-style). Only at a non-
        # terminal MY-perspective leaf (the 2-ply horizon = start of my next
        # turn), where the obs has a select to encode. V predicts P(I win).
        if (self.value_net is not None and self.v_scale
                and cur.result == -1 and cur.yourIndex == yi):
            from engine.obs import encode as _encode  # lazy: keeps base agent numpy-free
            enc = _encode(search_obs)
            if enc is not None:
                score += self.v_scale * float(self.value_net(enc["state"]))

        # Terminal: cur.result is the winning player index, or -1.
        if cur.result == yi:
            score += WIN_BONUS
        elif cur.result == (1 - yi):
            score -= WIN_BONUS

        return score

    def _sanitize(self, chosen, sel) -> list[int]:
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

    def _rollout_eval(self, root_id, first_choice, yi, start_turn, baseline):
        """Step ``first_choice`` from the root, then keep advancing the forked sim
        with the heuristic up to the configured horizon, and score the resulting
        board. Rolling forward lets "attach energy now, then attack" outscore
        "attack now", which a 1-ply state-eval cannot see.

        Horizon (``self.plies``):
          1 — stop at the end of MY turn (``turn`` advances or the seat changes).
              The opponent's turn is never simulated.
          2 — keep going through the opponent's full turn (the heuristic pilots
              the determinized opponent) and stop at the START OF MY NEXT TURN
              (``turn >= start_turn + 2``). The eval then reflects the opponent's
              reply: a return KO shows up as a prize given back, and damage I
              take shows up as lower board HP. ``turn`` is a global per-seat
              counter, so this boundary is exact even when my own attack forces
              an opponent sub-decision mid-turn (``turn`` stays put for those)."""
        db = get_card_db()
        try:
            st = search_step(root_id, list(first_choice))
        except Exception:
            return None
        sid = st.searchId
        obs = st.observation
        stop_turn = start_turn + self.plies  # 1 -> end of my turn; 2 -> my next turn
        for _ in range(self.rollout_depth):
            cur = obs.current
            if cur is None or cur.result != -1:
                break
            if obs.select is None:
                break
            if self.plies == 1:
                # Legacy 1-ply horizon: stop the instant it is no longer my turn.
                if cur.turn != start_turn or cur.yourIndex != yi:
                    break
            else:
                # 2-ply: roll through the opponent's turn; stop at my next turn.
                # Pilot whichever seat is to move (the heuristic reads yourIndex),
                # so the opponent's reply is simulated on the determinized board.
                if cur.turn >= stop_turn:
                    break
            sel = obs.select
            if len(sel.option) == 0:
                break
            action = _heur_sanitize(self._pilot_choose(sel, obs, db), sel)
            try:
                st = search_step(sid, action)
            except Exception:
                break
            sid = st.searchId
            obs = st.observation
        return self._evaluate(obs, yi, baseline)

    def _search_choice(self, obs):
        """Choose an option index. Default to the heuristic's pick; override only
        when search's rollout shows another option is materially better. Returns
        None on any error (caller falls back to the heuristic)."""
        sel = obs.select
        n = len(sel.option)
        yi = obs.current.yourIndex
        start_turn = obs.current.turn

        # Baseline = root board, for delta-scoring (damage dealt vs this).
        opp_root = obs.current.players[1 - yi]
        baseline = {"opp_hp": _pokemon_hp_sum(opp_root)}

        # Heuristic's preferred index (our prior / safe default), with ATTACK
        # options ranked by true dynamic damage when dynamic_attack is on.
        db = get_card_db()
        heur_idx = _heur_sanitize(self._pilot_choose(sel, obs, db), sel)
        heur_i = heur_idx[0] if heur_idx else 0

        # Average each option's rollout score over `self.samples` independent
        # determinizations (fresh hidden cards / opponent draws each time). Each
        # sample is its own search context: begin -> roll every option -> end.
        agg = [0.0] * n
        cnt = [0] * n
        deadline = (perf_counter() + self.time_budget) if self.time_budget else None
        # Score the heuristic's pick FIRST so that, if the per-move budget cuts us
        # short, we still have its baseline and can compare whatever we did score.
        # Unscored options stay None -> they can't override, so the agent degrades
        # gracefully toward the heuristic under time pressure. Even a single
        # high-option turn can blow the budget within ONE sample, so the deadline
        # is checked per option, not just per sample.
        order = [heur_i] + [i for i in range(n) if i != heur_i]
        out_of_time = False
        for s_i in range(self.samples):
            if deadline is not None and s_i > 0 and perf_counter() > deadline:
                break
            try:
                yd, yp, od, op, oh, oa = self._determinize(obs)
                root = search_begin(obs, yd, yp, od, op, oh, oa)
            except Exception:
                continue
            try:
                root_id = root.searchId
                for i in order:
                    if deadline is not None and cnt[heur_i] > 0 and perf_counter() > deadline:
                        out_of_time = True
                        break
                    s = self._rollout_eval(root_id, [i], yi, start_turn, baseline)
                    if s is not None:
                        agg[i] += s
                        cnt[i] += 1
            finally:
                try:
                    search_end()
                except Exception:
                    pass
            if out_of_time:
                break

        scores: list[float | None] = [
            (agg[i] / cnt[i]) if cnt[i] else None for i in range(n)
        ]

        base = scores[heur_i] if (0 <= heur_i < n and scores[heur_i] is not None) else None
        if base is None:
            # Could not score the heuristic's pick; trust the heuristic.
            return heur_i

        best_i, best_score = heur_i, base
        for i in range(n):
            s = scores[i]
            if s is None:
                continue
            if s > best_score + self.override_margin:
                best_score, best_i = s, i
        return best_i

    # ---- agent entrypoint ---------------------------------------------

    def __call__(self, obs_dict: dict) -> list[int]:
        obs = to_observation_class(obs_dict)
        if obs.select is None:  # deck-selection branch (kaggle path)
            return self.deck or default_deck()

        sel = obs.select
        n = len(sel.option)
        # Delegate non-strategic / multi-select / forced decisions.
        if obs.current is None or not self._learnable(sel, n):
            return heuristic_agent(obs_dict)

        best_i = self._search_choice(obs)
        if best_i is None:
            return heuristic_agent(obs_dict)  # robust fallback
        return self._sanitize([best_i], sel)
