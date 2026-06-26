# S0 — Honest non-mirror evaluation harness

- **Provenance:** [replay analysis](replay-81844919-analysis.md) §"what it proves" —
  mirror tournaments are self-referential; the ladder (600) disagreed with our
  internal #1–2 ranking. We needed an eval that can actually see our weaknesses.
- **Improves:** evaluation validity → **Model Score** (consistency & robustness become
  *measured*, not assumed). Prerequisite for every other strategy.
- **How:**
  - `scripts/exp_gauntlet.py` — our deck (chosen config) vs a diverse, strongly-piloted
    opponent set, **both seats**, multi-seed, Wilson **lb95**, hang-proofed
    (`max_steps=4000` + per-chunk future timeout). Config registry so every variant is
    compared against the *same* gauntlet. `--only` to focus on one opponent.
  - `scripts/diag_robustness.py` — fast self-play instrumentation of the replay's
    failure modes: **never-benched rate**, **fragile rate** (≤1 Pokémon in play at an
    end-of-turn after T1), **avg end-of-turn hand**, win% by seat.
- **Hypothesis:** an opponent-diverse, high-n eval reveals real strength and prevents
  noise- and over-fit-driven conclusions.
- **Measured:** baseline vs strong peer `mega_starmie_ex` (plies=2) = **51.0%**
  (lb95 46.6%, n=500); vs the 4-deck gauntlet ≈ **77%** aggregate (n=600). Intrinsic
  (baseline, n=80): never-benched **15.0%**, fragile **41.9%**, avg hand **4.30**.
- **Verdict:** **ACCEPTED (method).** All later decisions use this harness at n≥500.
- **Rubric:** Model Score (rigor/robustness), Report Score (reproducible figures/tables).
