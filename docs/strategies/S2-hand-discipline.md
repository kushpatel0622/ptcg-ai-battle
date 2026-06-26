# S2 — Hand-size discipline vs Resentful Refrain

- **Provenance:** [replay](replay-81844919-analysis.md) — an 8-card hand fed the
  mirror's **Resentful Refrain (50 × opp hand) = 400 dmg**. Refrain is the mirror's
  win condition and it is *in our own deck*.
- **Improves:** robustness vs the mirror's main weapon → **Model Score**.
- **How:** two mechanisms tried:
  1. `w_handpen` eval term — penalize my hand size at the leaf when an opponent
     in-play Pokémon can use Resentful Refrain (attack id `1240`).
  2. realistic `opp_model` in the 2-ply rollout (deal the opponent a real meta deck
     so the search *sees* a Froslass + Refrain threat).
  Configs: `discipline` (`opp_model=mega_starmie_ex, w_handpen=40`), `oppmodel`.
- **Hypothesis:** smaller end-of-turn hands vs Froslass; better going-first mirror.
- **Measured (vs strong peer, both seats):** `discipline` **44.5%** (n=200),
  `oppmodel` **46.0%** (n=200), `robust` (develop+discipline+oppmodel) **49.0%**
  (n=200) — none beat baseline (≈51% @ n=500).
- **Verdict:** **REJECTED.** `w_handpen` is frequently **inert** (the
  opp_can_refrain gate is constant across the options being compared, and only fires
  when a 1240 attacker is actually in play); `opp_model` added nothing measurable.
- **Rubric:** Model Score (measured; documents a plausible idea that didn't pay off).
