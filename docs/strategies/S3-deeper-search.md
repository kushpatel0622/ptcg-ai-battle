# S3 — Deeper search (spend the time budget)

- **Provenance:** the per-game time budget is large (replay `remainingOverageTime`
  ≈ 600, barely moved; we use ~2–3 s/game) — lots of unused compute. The user asked
  to "go much deeper than 2-ply."
- **Improves:** tactical strength/consistency → **Model Score**.
- **How:** generalized `SearchTeacher.plies` from {1,2} to any depth
  (`self.plies = max(1,int(plies))`, `rollout_depth = 40 + 70*plies`, opp_model/samples
  gated on `plies>=2`). Tested `develop3` (= develop terms at `plies=3`: my turn →
  opp turn → my turn).
- **Hypothesis:** seeing one more turn of the opponent improves play.
- **Measured (vs strong peer):** `develop3` **46.5%** (n=200) — below baseline
  (≈51%) and below 2-ply `develop` (50% @ n=200).
- **Verdict:** **REJECTED.** Going deeper makes the **heuristic-piloted rollout's
  errors compound** (the rollout pilot is weak, so more simulated turns add more
  error than signal), and the leaf parity shifts. 2-ply remains best.
- **Note:** a *better rollout pilot* (not just more depth) would be the real lever
  for using the time budget — a candidate for future work (e.g., shallow search as
  the rollout policy), but expensive and unproven.
- **Rubric:** Model Score (measured; explains *why* deeper ≠ better here).
