# S1 — Bench-development reward + fragility penalty (eval terms)

- **Provenance:** [replay](replay-81844919-analysis.md) — a lone basic with no bench
  is one KO from a board-out loss; the agent didn't value being on board.
- **Improves:** consistency/robustness (don't depend on a perfect opener) → **Model
  Score**; better use of bench-builders → **Deck Score**.
- **How:** new `SearchTeacher` eval terms (in `rl/` + `submission/search_teacher.py`,
  default 0):
  - `w_bench` — reward per benched Pokémon, capped at `bench_target` (develop a board).
  - `fragile_penalty` — subtracted when my in-play Pokémon ≤1 at the rollout leaf
    (one KO from "no active Pokémon").
  Config `develop` = `w_bench=60, fragile_penalty=600, bench_target=3`. Sweep tried
  `fragile_penalty ∈ {600,1000,1500}`, `w_bench ∈ {60,120}`, `bench_target ∈ {2,3}`.
- **Hypothesis:** fewer turn-1/2 board-out losses, especially going first.
- **Measured (vs strong peer, both seats):**
  | n | baseline | develop | dev_f1000 |
  |---|---|---|---|
  | 200 | 45.0% | 50.0% (looked +5) | — |
  | **500** | **51.0%** | **47.4%** | 45.3% (n=300) |
  Intrinsic (n=80): never-benched 15.0%→13.1% (noise), fragile **41.9%→45.0% (worse)**,
  hand 4.30→4.24. The terms barely engaged.
- **Verdict:** **REJECTED.** The +5pt was n=200 noise; at n=500 it's ≤ baseline.
  *Why it failed mechanically:* the terms only affect single-choice (`_learnable`)
  decisions, but **benching is usually a forced/multi-select setup decision delegated
  to the heuristic** — so the eval can't actually steer board development. Code kept
  (default-off) for the record.
- **Rubric:** Model Score (a measured negative result is rigor, not failure).
