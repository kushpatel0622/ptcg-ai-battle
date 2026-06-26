# S8 — Config/eval tuning (Phase 2, on top of the improved pilot)

- **Provenance:** Phase 2 of "max out the shipped submission" — after adopting the
  improved rollout pilot ([S7](S7-rollout-pilot.md)), tune the search/eval knobs for
  `mega_starmie_ex_2` vs the strong peer.
- **Improves:** search/eval calibration → **Model Score**. Deployable (pure search).
- **How:** screen 7 variants on top of `rollout_policy="improved"`, vs the peer at
  **n=600**, then confirm the top ones at high n. Knobs:
  - `override_margin ∈ {5, 50, 100}` (how much better a rollout must look before the
    search overrides the heuristic prior; default 20),
  - `w_dmg ∈ {5, 10}` (weight on damage-dealt; default 2 — higher = more aggressive),
  - `w_hp = 2` (own-board-HP weight; default 1),
  - `samples = 3` (average over determinizations; default 1).
- **Hypothesis:** a slightly more aggressive / denoised eval edges the aggro mirror.
- **Screen (n=600 vs peer):**
  | config | win% | lb95 |
  |---|---|---|
  | **imp_wdmg10** (w_dmg=10) | **53.2%** | 49.2% |
  | imp_s3 (samples=3) | 51.0% | 47.0% |
  | imp_m5 / imp_m50 (override_margin 5/50) | 49.7% | 45.7% |
  | imp_m100 | 49.0% | 45.0% |
  | imp_wdmg5 | 49.5% | 45.5% |
  | imp_whp2 | 48.7% | 44.7% |
  | improved (base) | 47.5% | 43.5% |
- **Confirmation (running):** baseline vs improved vs `imp_wdmg10` vs `imp_s3` at
  **n=1200** vs peer + `imp_wdmg10` full-gauntlet no-regression check →
  `data/opt/phase2_confirm.txt`. The +5.7pt screen lead for `imp_wdmg10` may be n=600
  noise; only the high-n confirmation (and field check — w_dmg=10 over-valuing damage
  could misplay vs other decks) decides whether it ships.
- **Confirmation (n=1200 vs peer):** plain **improved 52.5%** (lb95 49.7%) > `imp_wdmg10`
  **51.3%** > `imp_s3` 50.4% > baseline 48.8%. The screen's `imp_wdmg10` lead was n=600
  noise — at n=1200 it fell BELOW the plain improved pilot. `imp_wdmg10` field = 84.2% (no
  diff). **No eval-weight/sample/margin tweak beats the plain improved pilot.**
- **Verdict: REJECTED (keep default eval weights).** Phase 2 adds nothing on top of S7.
  The improved pilot with default weights is the final config.
- **Rubric:** Model Score (systematic high-n tuning; the screen→confirm gap is itself the
  n=200/600-is-noise lesson, re-confirmed).
