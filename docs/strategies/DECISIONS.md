# Decisions — accepted / rejected (with evidence)

Conservative rule: a change is **accepted** only if it beats the incumbent at
**n≥500** with a Wilson **lb95** margin (engine RNG is unseeded; n=200 lies).
"Don't re-litigate" the rejected ones without new evidence.

| # | Change | Decision | Evidence | Detail |
|---|---|---|---|---|
| D1 | Remove dead `engine.obs`/value_net from submission; clean package; reproducible build | **ACCEPTED** | self-contained verified, 10 games 0 errors | shipped |
| D2 | Evaluate on **non-mirror** gauntlet, both seats, n≥500 | **ACCEPTED (method)** | mirror eval was self-referential (ladder 600 ≠ internal #1) | [methodology.md](methodology.md) |
| D3 | `develop` eval terms (bench reward + fragility penalty) | **REJECTED** | 47.4% ≤ baseline 51.0% @ n=500 (looked +5pt @ n=200 = noise) | [S1](S1-bench-fragility.md) |
| D4 | Hand-discipline penalty `w_handpen` | **REJECTED** | 44.5% @ n=200, no help; often inert | [S2](S2-hand-discipline.md) |
| D5 | Deeper search (`plies=3`) | **REJECTED** | 46.5% — heuristic-rollout errors compound | [S3](S3-deeper-search.md) |
| D6 | Deck `2c` (−2 Energy Search +2 Ultra Ball) | **REJECTED** | 41.5% — hurt tempo/energy | [deck-2c](deck-2c-consistency.md) |
| D7 | Keep **baseline config** (`plies=2, dynamic_attack`) as champion | **ACCEPTED** | best measured agent config (~51% vs peer) | — |
| D8 | Realistic `opp_model` in 2-ply rollout | **REJECTED** | 46% @ n=200 — no gain | [S2](S2-hand-discipline.md) |
| D9 | Keep `mega_starmie_ex_2` as the deck (vs all candidates) | **ACCEPTED (so far)** | high-n deck tournament: 76.8%, top deck + best peer matchup 57% | [deck-tournament-results.md](deck-tournament-results.md) |
| D10 | Config `samples=3` / `margin5` | **REJECTED** | 74.2% / 76.2% ≤ champ 76.3% @ n=600 | round 2 |
| D11 | Equal-weight aggregate fitness | **REJECTED (replaced)** | masked a peer regression (promoted a deck with mega 47% vs 57%) → over-fit to easy decks | [S5](S5-peer-primary-fitness.md) |
| D12 | **Peer-primary fitness** (peer 2× games; field no-regression guard) | **ADOPTED** | optimizes the discriminating matchup; anti-over-fit | [S5](S5-peer-primary-fitness.md) |
| — | round-4 promotion `Team Rocket Ball + Night` | **RETRACTED** | noise/over-fit artifact; champion reset to baseline | [S5](S5-peer-primary-fitness.md) |
| D13 | GPU value-net leaf eval (`value_net`+`v_scale`) | **REJECTED** | peer: 49.0% base vs 46.5%/47.5% (no gain); also unshippable (numpy-free) | [S6](S6-gpu-value-net.md) |
| D14 | Mirror is a structural ~50% coinflip; no edit beats baseline on the peer | **FINDING** | ~30 challengers all 44–51% peer @ n=300 → `mega_starmie_ex_2` near-optimal | [finding-mirror-coinflip.md](finding-mirror-coinflip.md) |
| D15 | Deck choice: baseline `mega_starmie_ex_2` | **ACCEPTED** | n=600 confirm: baseline 49.7% > cand_teamrocket 48.0% > cand_gust 43.0%; 66 challengers, none better | [SUMMARY.md](SUMMARY.md) |
| D16 | **Improved rollout pilot** (`rollout_policy="improved"`) | **ADOPTED & SHIPPED** | n=2800 each: ~51.0% vs ~48.3% baseline = **+2.7pt (z≈2.0, p≈0.04)**, never worse, holds field 84% | [S7](S7-rollout-pilot.md) |
| D17 | Phase 2 eval/search tuning (w_dmg=10, samples=3, override_margin) | **REJECTED** | n=1200: nothing beats the plain improved pilot (52.5%); imp_wdmg10 screen lead was noise | [S8](S8-config-tuning.md) |
| D18 | **FINAL shipped config** = `mega_starmie_ex_2` + `SearchTeacher(plies=2, samples=1, dynamic_attack=True, time_budget=1.0, rollout_policy="improved")` | **SHIPPED** | rebuilt + verified: 0 errors, numpy-free | [SUMMARY.md](SUMMARY.md) |
| D19 | Adversarial review caught: bench-when-thin was DEAD CODE (PLAY has `index` not `cardId`); +2.7pt was lethal-KO alone | **FIXED** | refactored to honest lethal-only; corrected docs | [S7b](S7b-bench-fix.md) |
| D20 | `improved_bench` (working bench-when-thin) | **REJECTED** | n=1200: 49.1% < improved 51.1% — fixing the bench to fire HURT (re-confirms S1) | [S7b](S7b-bench-fix.md) |
| D21 | **Improved (lethal-KO) pilot, pooled significance** | **CONFIRMED** | n=4000 each: 51.0% vs baseline 48.4% = +2.6pt, z≈2.3, **p≈0.02** | [S7b](S7b-bench-fix.md) |

<!-- monitoring ticks append champion promotions / new rejections below -->

## Open / under test (autonomous loop)
- LLM-proposed consistency edits (e.g., add Lillie's Clefairy ex, Great Ball,
  Night Stretcher+Energy Retrieval) — queued, being measured at n=600.
- Config tweaks: `samples=3`, `override_margin=5`, `w_dmg=6` — queued.
- Base-deck tournament: which of our decks is strongest vs the gauntlet — measuring.
- GPU value-net leaf eval — planned (historically lost; re-testing honestly).
