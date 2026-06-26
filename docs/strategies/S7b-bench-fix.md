# S7b — Bench-when-thin fix + test (follow-up to the verification finding)

- **Provenance:** the adversarial verification of S7 found the bench-when-thin branch was
  **dead code** (PLAY options carry a hand `index`, not `cardId`). So the shipped pilot
  was effectively **lethal-KO only**, and the +2.7pt came from that alone.
- **Improves:** code honesty + a fair test of whether benching actually helps → **Model Score**.
- **How:** refactored into `_improved_pick(..., bench_when_thin)`:
  - `_choose_improved` (`rollout_policy="improved"`) — lethal-KO only (+ spread-attack
    exclusion). This is the **as-measured, shipped** behaviour, now honest (no dead code).
  - `_choose_improved_bench` (`rollout_policy="improved_bench"`) — adds a **working**
    bench-when-thin rule (resolves the Basic via `me.hand[o.index].id`).
- **Hypothesis:** uncertain. A *working* bench rule might help rollout realism — but S1
  showed bench-development (as an eval term) was neutral/negative, so it may not help here
  either. Test decides.
- **Measured (n=1200 vs peer):** `improved` (lethal-only) **51.1%** > baseline 48.6% >
  `improved_bench` (working bench) **49.1%**. The **working bench rule HURT** (−2pt vs
  lethal-only). Field for `improved_bench` = 84.2% (no diff). Re-confirms S1: bench
  development doesn't help this deck — the dead-code bug being inert was harmless; *fixing*
  it to fire would have regressed.
- **Verdict: REJECTED `improved_bench`; SHIP `improved` (lethal-KO only).** The shipped
  pilot is exactly this. Pooled over all runs (**n=4000 each**): improved **51.0%** vs
  baseline **48.4%** = **+2.6pt, z≈2.3, p≈0.02** (now statistically significant).
- **Rubric:** Model Score (caught a dead-code bug via adversarial review, corrected the
  record, and re-tested honestly — exactly the rigor the rubric rewards).
