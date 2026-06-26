# S5 — Peer-primary fitness fix (anti-over-fit objective)

- **Provenance:** at round 4 the loop **promoted** `llm:anthropic:Team Rocket Ball + Night`
  (agg 77.3%) — but it was **worse on the peer matchup (mega 47%)** than baseline
  (57%), trading the hard, discriminating matchup for easy decks we already win
  80–97%. The promotion fired because the champion's *same-round* measurement dipped
  to 72% (n=150 noise). The **equal-weight aggregate masked a peer regression** — the
  exact single-/easy-matchup over-fit the competition robustness rubric penalizes.
- **Improves:** the optimization **objective** → **Model Score** (soundness +
  robustness): optimize the matchup closest to real strong ladder decks, don't
  inflate the score on already-won opponents.
- **How:** rewrote `scripts/opt_loop.py::evaluate` to **peer-primary**:
  - the peer (`mega_starmie_ex`) gets **2× games** (tighter CI on the matchup that matters);
  - **fitness = peer win%** (primary); the other 3 decks form a **field no-regression guard**.
  - Promotion now requires: `challenger.peer_wr > champ.peer_wr` **and**
    `peer_lb95 ≥ champ.peer_wr` (confident peer gain) **and**
    `field_wr ≥ champ.field_wr − 3pt` (don't break the field).
  - **Reset champion to baseline `mega_starmie_ex_2`** (known best on the peer); the
    de-promoted deck is re-queued to be re-judged under the corrected objective.
- **Hypothesis:** the search now climbs the *peer* matchup (~50–57% headroom) without
  trading it away, producing a deck that's genuinely stronger vs strong opponents.
- **Measured:** `evaluate()` validated (peer gets 2× games, peer_wr/field_wr/lb95
  correct). Loop relaunched 2026-06-25 ~13:25 with peer-primary fitness. Results to follow.
- **Verdict:** **ADOPTED (method fix).** Supersedes the equal-weight aggregate used in
  rounds 1–4 (whose `Team Rocket Ball + Night` promotion is **retracted** as a
  noise/over-fit artifact).
- **Rubric:** Model Score (a corrected, defensible objective; documents the failure
  mode and the fix — methodological rigor).
