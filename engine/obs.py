"""Observation & action encoding for the neural policy.

Turns a parsed ``Observation`` into fixed-size numpy arrays:

  encode(obs) -> {
      "state":   float32[STATE_DIM],      # global board + selection context
      "options": float32[n_options, OPT_DIM],  # one row per legal option
      "n":       int,                     # number of legal options
  }

The policy will score each option row against the state vector (a pointer-style
head) and pick indices into ``options``. Because the engine only ever offers
legal options, the option rows ARE the legal action set — no extra mask needed
beyond padding to a max length at batch time.

This module is intentionally numpy-only so the same code can run inside the
CPU-only submission.
"""
from __future__ import annotations

import numpy as np

import engine  # noqa: F401  (puts submission/ on sys.path so `cg` imports)
from cg.api import to_observation_class

from engine.cards import CARD_FEAT_DIM, get_card_db

# --- enum cardinalities (sized with headroom; new enum members may be appended) ---
SELTYPE_N = 11   # SelectType 0..10
CONTEXT_N = 49   # SelectContext 0..48
OPT_TYPE_N = 17  # OptionType 0..16
AREA_N = 13      # AreaType 1..12 (index 0 unused)

# Per-option row: optType one-hot + referenced-card features + attack dmg +
#                 area one-hot + (is_self, is_opp) + number value
OPT_DIM = OPT_TYPE_N + CARD_FEAT_DIM + 1 + AREA_N + 2 + 1  # = 64

# State: selType one-hot + context one-hot + 4 select counts + 8 turn flags +
#        2x13 player summaries + 2x card-features (self/opp active)
STATE_DIM = SELTYPE_N + CONTEXT_N + 4 + 8 + 2 * 13 + 2 * CARD_FEAT_DIM  # = 158


def _onehot(idx, n: int) -> list[float]:
    v = [0.0] * n
    if idx is not None and 0 <= int(idx) < n:
        v[int(idx)] = 1.0
    return v


def _clip01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def _active(player):
    a = player.active[0] if player.active and len(player.active) > 0 else None
    return a


def _player_summary(p) -> list[float]:
    a = _active(p)
    if a is not None:
        hp_ratio = (a.hp / a.maxHp) if a.maxHp else 0.0
        maxhp = a.maxHp / 300.0
        energy = len(a.energies) / 6.0
    else:
        hp_ratio = maxhp = energy = 0.0
    return [
        _clip01(hp_ratio), _clip01(maxhp), _clip01(energy),
        _clip01(len(p.bench) / 5.0), _clip01(p.deckCount / 60.0),
        _clip01(p.handCount / 15.0), _clip01(len(p.discard) / 60.0),
        _clip01(len(p.prize) / 6.0),
        float(p.poisoned), float(p.burned), float(p.asleep),
        float(p.paralyzed), float(p.confused),
    ]


def _active_feats(p, db) -> np.ndarray:
    a = _active(p)
    if a is not None and a.id is not None:
        return db.features(a.id)
    return np.zeros(CARD_FEAT_DIM, dtype=np.float32)


def encode_state(obs, db) -> np.ndarray:
    sel, st = obs.select, obs.current
    yi = st.yourIndex
    me, opp = st.players[yi], st.players[1 - yi]
    out: list[float] = []
    out += _onehot(int(sel.type), SELTYPE_N)
    out += _onehot(int(sel.context), CONTEXT_N)
    out += [
        _clip01(sel.minCount / 8.0), _clip01(sel.maxCount / 8.0),
        _clip01(sel.remainDamageCounter / 20.0), _clip01(sel.remainEnergyCost / 6.0),
    ]
    out += [
        _clip01(st.turn / 60.0), _clip01(st.turnActionCount / 20.0),
        float(yi), 1.0 if st.firstPlayer == yi else 0.0,
        float(st.supporterPlayed), float(st.stadiumPlayed),
        float(st.energyAttached), float(st.retreated),
    ]
    out += _player_summary(me)
    out += _player_summary(opp)
    arr = np.asarray(out, dtype=np.float32)
    arr = np.concatenate([arr, _active_feats(me, db), _active_feats(opp, db)])
    if arr.shape[0] != STATE_DIM:
        raise ValueError(f"state dim {arr.shape[0]} != STATE_DIM {STATE_DIM}")
    return arr


def encode_option(opt, db, yi: int) -> np.ndarray:
    out: list[float] = []
    out += _onehot(int(opt.type), OPT_TYPE_N)
    out += list(db.features(opt.cardId) if opt.cardId is not None
                else np.zeros(CARD_FEAT_DIM, dtype=np.float32))
    out += [_clip01((db.attack_damage(opt.attackId) / 300.0) if opt.attackId is not None else 0.0)]
    area = opt.area if opt.area is not None else opt.inPlayArea
    out += _onehot(int(area) if area is not None else None, AREA_N)
    is_self = 1.0 if (opt.playerIndex is not None and opt.playerIndex == yi) else 0.0
    is_opp = 1.0 if (opt.playerIndex is not None and opt.playerIndex != yi) else 0.0
    out += [is_self, is_opp]
    out += [_clip01((opt.number / 20.0) if opt.number is not None else 0.0)]
    arr = np.asarray(out, dtype=np.float32)
    if arr.shape[0] != OPT_DIM:
        raise ValueError(f"option dim {arr.shape[0]} != OPT_DIM {OPT_DIM}")
    return arr


def encode(obs):
    """Encode a parsed Observation or raw obs_dict. Returns None at deck select."""
    if isinstance(obs, dict):
        obs = to_observation_class(obs)
    if obs.select is None or obs.current is None:
        return None
    db = get_card_db()
    yi = obs.current.yourIndex
    options = obs.select.option
    if len(options) == 0:
        opt_arr = np.zeros((0, OPT_DIM), dtype=np.float32)
    else:
        opt_arr = np.stack([encode_option(o, db, yi) for o in options])
    return {"state": encode_state(obs, db), "options": opt_arr, "n": len(options)}
