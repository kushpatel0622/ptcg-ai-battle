# Changelog (append-only, timestamped)

All times EST, 2026-06-25 unless noted. Newest at the bottom within a day.

## 2026-06-25

- **~10:25 (prior session)** — Submission cleanup: removed dead `engine.obs` import
  + unused `value_net` machinery from `submission/search_teacher.py`; removed
  redundant `submission/sample_submission/`; added reproducible build
  `scripts/build_submission.py` + isolated verifier `scripts/verify_tarball_isolated.py`.
  Rebuilt + verified `submission.tar.gz` (self-contained, numpy-free, 10 games 0 errors).
- **~11:00** — Analyzed submitted replay `81844919` → `replay-81844919-analysis.md`.
  Root cause of the loss + the "mirror tournaments are self-referential" finding.
- **~11:10** — Built `scripts/exp_gauntlet.py` (config-driven non-mirror gauntlet,
  multi-opp, Wilson lb95, both seats, hang-proofed) and `scripts/diag_robustness.py`
  (intrinsic metrics). → `S0-eval-harness.md`.
- **~11:20** — Added robustness eval terms to `rl/search_teacher.py` AND
  `submission/search_teacher.py` (default-off): `w_bench`, `fragile_penalty`,
  `bench_target`, `w_handpen`; generalized `plies` to any depth. → `S1`, `S2`, `S3`.
- **~11:30** — Created `decks/mega_starmie_ex_2c.csv` (−2 Energy Search +2 Ultra Ball).
  → `deck-2c-consistency.md`.
- **~11:40** — High-n reruns (n=500) REVERSED the earlier n=200 "+5pt": baseline
  51.0% vs develop 47.4%. Eval terms / depth-3 / deck-2c all rejected. Recorded the
  measurement-discipline lesson in `methodology.md`.
- **11:53** — Launched autonomous optimizer `scripts/opt_loop.py` (until 16:25,
  n=600/challenger vs 4-deck gauntlet, lb95-gated promotion). → `S4-autonomous-search.md`.
  Champion start: baseline `mega_starmie_ex_2` @ 76.8% aggregate.
- **~11:55** — Built `scripts/gen_challengers_llm.py`; ran it: OpenAI gpt-4o +
  Anthropic sonnet each proposed 3 legal card-swaps (both flagged adding a
  consistency basic, Lillie's Clefairy ex); Sakana/fugu no clean JSON; xAI/Grok 403
  (no credits). 6 LLM challengers queued for measurement.
- **~12:1x** — Created this `docs/strategies/` tracking folder (file-per-strategy).

- **12:41 (tick 1)** — Health OK (optimizer alive, 11 workers). Rounds 1–2 done:
  deck tournament → `mega_starmie_ex_2` confirmed best base deck (76.8%, best peer
  matchup 57%); `mega_starmie_ex`/`wildcard_best` near-ties (76–77%) but **not
  promoted** (lb95 guard held); other archetypes ≥20pt worse; config tweaks
  (samples3/margin5) no gain. Full table → [deck-tournament-results.md](deck-tournament-results.md).
  Refilled +5 LLM challengers (consistency-basic / Ribombee-search themes). GPU track
  deferred (before 13:30). No champion change.

- **13:25 (tick 2)** — Rounds 3–4 ran. Round 4 **promoted** `Team Rocket Ball + Night`
  on a noisy low champion round, but it **regressed the peer (mega 47% vs 57%)** —
  exposing a flaw: the equal-weight aggregate masked peer regressions (over-fit to
  easy decks). **Fix ([S5](S5-peer-primary-fitness.md)):** rewrote `opt_loop.evaluate`
  to **peer-primary** (peer gets 2× games; fitness = peer win%; field = no-regression
  guard ≤3pt). Promotion now needs a confident peer gain + no field regression.
  **Stopped** the loop (targeted kill PID 30324), **reset champion to baseline**,
  re-queued the de-promoted deck + fresh LLM ideas, **relaunched** with peer-primary
  fitness. Retracted the round-4 promotion as a noise/over-fit artifact.

- **14:14 (tick 3)** — Peer-primary loop healthy (1 instance, 12 procs), rounds 1–3:
  **every LLM consistency edit REGRESSED the peer** (mega 38–46% vs baseline ~54%) →
  none promoted (the fix is working as intended). Champion holds **baseline
  mega_starmie_ex_2** (peer ~47–54% across rounds = noise band, field ~81–86%).
  **GPU track ([S6](S6-gpu-value-net.md)):** patched gen_value_data to champion deck →
  200 games / 19.7k states → trained `ValueNet` on **CUDA** (val acc **73%**) →
  leaf-eval (v_scale 0/0.5/1.0 vs peer) running. _Caveat:_ value net can't ship
  (numpy-free submission). **Redirected LLM prompt to MIRROR-beating ideas** (Boss's
  disruption, +1 Mega Signal tempo, Lillie's Pearl vs Refrain, energy accel) → 8 new
  challengers queued (Sakana/fugu parsed this time). No champion change.

- **14:51 (tick 4)** — **GPU value-net REJECTED** ([S6](S6-gpu-value-net.md)): leaf-eval
  vs peer — baseline 49.0% vs v_scale 0.5→46.5% / 1.0→47.5% (no gain; unshippable anyway).
  Peer-primary rounds 3–4: systematic swaps + mirror-focused LLM ideas (Arven Sandwich,
  +1 Mega Signal, +1 Boss's, Energy Switch, Scramble Switch) ALL ~44–50% on the peer →
  none beat baseline. **PLATEAU finding**: the near-mirror is a structural **~50% coinflip**;
  baseline `mega_starmie_ex_2` is at/near optimum ([finding-mirror-coinflip.md](finding-mirror-coinflip.md)).
  Champion holds baseline. Refilled mirror-focused challengers. 1 opt_loop instance, healthy.

- **15:29 (tick 5)** — Champion drifted to `llm:sakana:gust-pressure` (max Boss's Orders,
  PEER 48.0%) — **another noise promotion** inside the ~50% coinflip band (best peer_wr in
  ALL history = 0.527, every candidate within n=300 noise of baseline). Rounds 5–7: all
  challengers 39–49% peer, no genuine gain. The peer-primary guard *reduces* but doesn't
  *eliminate* residual noise drift at n=300. Saved top candidate decks (`decks/cand_gust.csv`,
  `decks/cand_teamrocket.csv`) so the FINAL WRAP can confirm them vs baseline at n≥600 and
  revert to baseline unless one genuinely beats it. Refilled challengers. 1 loop, healthy.

- **16:35 (FINAL WRAP)** — Loop stopped after 11 rounds / **66 challengers**. High-n
  (n=600) confirmation vs peer: **baseline 49.7%** (lb95 45.7%) > `cand_teamrocket` 48.0%
  > `cand_gust` 43.0% — both drifted "champions" are WORSE at honest n (noise promotions
  caught). **Decision: KEEP baseline `mega_starmie_ex_2`.** Submission rebuilt + verified
  (0 errors, numpy/torch never loaded, 3.8× timing margin). **No win-rate improvement
  found** — baseline confirmed near-optimal. Full recap → [SUMMARY.md](SUMMARY.md). Run complete.

- **19:04 — Phase 1: improved rollout pilot ADOPTED** ([S7](S7-rollout-pilot.md)). New
  `rollout_policy="improved"` (bank lethal KOs without overcommitting the hand; bench a
  Basic when the bench is empty). vs baseline at **n=1600 each**: improved **~49.8%** vs
  baseline **~47.9%** (+1.9pt, never worse across n=600 & n=1000 runs; not significant
  z≈1.1 but a principled, risk-free change). Field held (84.4%). **Launched Phase 2**:
  config/eval tuning (override_margin, w_dmg, w_hp, samples) on top of the improved pilot,
  n=600 screen → `data/opt/phase2_screen.txt`.

- **~19:40 — Phase 2 config tuning: no gain; FINAL config SHIPPED** ([S8](S8-config-tuning.md)).
  Confirmation n=1200 vs peer: plain improved pilot **52.5%** > imp_wdmg10 51.3% > imp_s3
  50.4% > baseline 48.8% — the screen's imp_wdmg10 lead was noise; **no eval-weight/sample
  tweak beats the plain improved pilot**. Kept default weights. **Vendored
  `rollout_policy="improved"` into the submission** (main.py + search_teacher.py),
  rebuilt + verified (0 errors, numpy/torch never loaded, 4.3× timing margin). Net result
  of Phases 1–2: a **real ~+2.7pt peer improvement (p≈0.04)** from the rollout pilot, now
  shipped. Adversarial verification workflow run on the final change.

- **~20:30 — Adversarial verification + bench-fix (FINAL).** A 3-reviewer workflow on the
  shipped change found **bench-when-thin was DEAD CODE** (PLAY options carry hand `index`,
  not `cardId`) — so the +2.7pt was from **lethal-KO banking alone**. Refactored to honest
  code (`_improved_pick` → `improved` = lethal-only, `improved_bench` = working bench), added
  spread-attack exclusion. Tested the *working* bench (n=1200): **49.1% < improved 51.1%** —
  fixing the bench HURT (re-confirms S1). **Kept `improved` (lethal-KO only).** Pooled over
  all runs (**n=4000 each**): improved **51.0%** vs baseline **48.4%** = **+2.6pt, p≈0.02**
  (significant). Submission rebuilt + re-verified (0 errors, numpy-free). Docs corrected
  ([S7](S7-rollout-pilot.md) correction, [S7b](S7b-bench-fix.md), [DECISIONS](DECISIONS.md) D19–D21).

- **02:31 (counter-training tick 1)** — Analyzed the 4 real ladder losses (3× Mega Lucario ex
  Fighting, 1× Iono/Bellibolt ex Lightning). **DECISIVE FINDING ([counter-analysis.md](counter-analysis.md)):**
  in equal-pilot sim our deck **BEATS** them (Lucario 75%, Bellibolt 81%, n=400) — because our
  agent **mispilots the opponents' decks** (the project's oldest trap). So these are NOT hard
  counters; the real losses are the **variance tail** of favorable matchups (slow/brick openings +
  opponent skill), and we **can't reliably train the matchup internally** (can't pilot their decks
  at the real level). Type-counter decks fail (gardevoir 2% mirror — our agent can't pilot them).
  mega_starmie_ex_2 remains best vs the counters. Skipped LLM refill this tick (counter-objective
  is mispilot-unreliable). Run continues to 08:00 (guard-protected); conclusion at the wrap.

- **03:24 (counter-training tick 2)** — Healthy, 0 promotions, 11 challengers tested; **no
  mirror-safe gem** (nothing beats the counters AND holds the mirror ≥50%). Confirms: champion
  `mega_starmie_ex_2` + improved pilot holds; no counter-tech to chase (counter-objective is
  mispilot-unreliable anyway). Stretched monitoring to ~60 min (stable; nothing actionable until wrap).

- **05:28 (counter-training tick 4)** — Healthy, still 0 promotions / 26 challengers. One
  candidate flagged: `swap -1122+1097` (cut 1 Pokégear, +1 Night Stretcher = recovery/recursion)
  scored counters 79.5% AND held mirror 52% (n=200). Counter # is mispilot-unreliable and 52%
  mirror is within champion noise, so likely not real — but saved as `decks/cand_nightstretcher.csv`
  for a high-n MIRROR confirmation at the final wrap (ship only if it confidently beats the
  champion on the mirror without regression).

- **06:30 (counter-training tick 5)** — A (likely-noise) promotion fired: `swap -1119+1097`
  (−1 Energy Search, +2nd Night Stretcher) — counters 80%, mirror 53%. 4 "gems" all cluster at
  mirror ~52% = the champion's mirror dipped that round (n=200 noise). BUT multiple top swaps add
  **Night Stretcher (recovery)** — a recurring theme worth a real check. Saved `cand_promoted.csv`
  (=swap -1119+1097). The WRAP will high-n (n≥800) MIRROR-confirm the +Night-Stretcher variants
  (cand_promoted, cand_nightstretcher) vs baseline; ship only if one confidently beats the champion
  on the mirror without regression.

- **07:22 — FINAL WRAP (counter-training).** Stopped the loop early (user wrap request). Overnight
  run = 41 challengers vs the real counters, **0 confident improvements**. High-n (n=800) MIRROR
  check of the recurring +Night-Stretcher variants: baseline 48.5% vs cand_promoted 50.5% (lb95
  47.0%) vs cand_nightstretcher 48.6% — **within noise, not shipped.** **Submission UNCHANGED**
  (mega_starmie_ex_2 + improved pilot). Conclusion in [counter-analysis.md](counter-analysis.md):
  the counters are NOT hard counters (we're favored in mispilot-inflated sim), prize-asymmetry
  isn't fixable without regressing elsewhere, best lever = own execution (shipped) + ladder volume.
  Counter-training run COMPLETE.

- **(post-handoff) EARLY-DEVELOPMENT RULE SHIPPED ([S9](S9-early-development.md)).** Move-by-move
  decode of the real losses (`scripts/replay_movelog.py`) → the lone-basic OPENING brick, with the
  agent holding Poffin/a 2nd basic and not playing them. Added `rollout_policy="improved_dev"`:
  in the opening (turn≤2), if <2 Pokémon in play, force Poffin/bench-a-basic. **Gating to the
  opening is the key** — always-on regressed the mirror −3.7pt; opening-gated is mirror-NEUTRAL
  (48.5% n1200) AND **+5.4pt vs Mega Lucario ex (73.3→78.7%, p≈0.03)**, the deck that caused 3/4
  losses. Deck swap +Great Ball REJECTED (−3.2pt mirror at n1500). **Shipped on mega_starmie_ex_2;
  rebuilt + verified (0 errors, numpy-free, 3.7× margin).** Submission now = improved_dev pilot.

<!-- monitoring ticks append promotions / new experiments below -->
