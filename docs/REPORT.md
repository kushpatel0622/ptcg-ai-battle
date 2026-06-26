# Pokémon TCG AI Battle — Strategy & Report Log

_Living document. Every strategy we try is recorded here with its **provenance**
(how it came to be), **what** it improves, **how**, the **hypothesis**, and the
**measured** before/after. Structure mirrors the competition's three scored
categories so the report writes itself._

> **Detailed audit trail:** every strategy/change has its own file under
> [`docs/strategies/`](strategies/README.md) — one file per experiment, plus a
> timestamped [CHANGELOG](strategies/CHANGELOG.md) and an accept/reject
> [DECISIONS](strategies/DECISIONS.md) matrix. Live run artifacts are in `data/opt/`.

## Evaluation categories (the rubric we are graded on)

| Category | What it rewards |
|---|---|
| **Model Score** | Clear articulation of approach + rationale for model/methods; originality & technical soundness; **consistency under repeated matches**; **robustness — not over-relying on specific initial states, matchups, or situational advantages**; performance within the track. |
| **Deck Score** | Clear deck concept that **aligns with the strategy**; effective selection & utilization of **key cards** to support the game plan. |
| **Report Score** | Logical, clear structure; effective **figures/charts/tables**. |

---

## 1. Baseline state (as of 2026-06-25)

- **Agent:** `SearchTeacher` — forward search over the bundled `cg` engine
  (determinize hidden info → roll each option to a 2-ply horizon with a
  heuristic pilot → score by Δ(prizes, damage, board-HP)). 0 learned params.
  Config: `plies=2, samples=1, dynamic_attack=True`.
- **Deck:** `mega_starmie_ex_2` — dual Mega Water line (Snorunt→**Mega Froslass ex**,
  Staryu→**Mega Starmie ex**), 8 basics, Water energy, draw/search Trainers.
- **Ladder score:** ~**600** (top decks ~**1367.4**). This is the win-based
  rating — the number we are trying to raise. [Model Score → track performance]

### 1.1 Why we are at 600 — evidence from replay `81844919`
Self-validation **mirror** game (both sides our own deck/agent), we went first, lost:
1. Opened with **only 1 basic** (Snorunt); a 2nd basic (Staryu) + a key attacker
   got **prized**. Never developed a bench all game (0 bench plays).
2. Ended turn 1 with a lone 70-HP Snorunt and a **fat 8-card hand**.
3. Opponent evolved **Mega Froslass ex** and used **Resentful Refrain
   (50 × hand = 50×8 = 400 dmg)** → one-shot KO → no Pokémon to promote → loss
   (rule: "no active Pokémon").

### 1.2 The methodology flaw this exposes
Our internal tournaments ranked this deck #1–2 — but they were **mirror/self-play**:
both sides shared the same blind spots (no bench discipline, fat hands), so the
ranking was self-referential and did **not** predict the ladder. → All evaluation
below uses **non-mirror, well-piloted, both-seat** matches. [Model Score → robustness]

---

## 2. Strategy log

> Template — copy for each new strategy.
> **Sx — title**
> - **Provenance:** what observation/evidence motivated it.
> - **Improves (weakness → rubric dim):**
> - **How (mechanism):**
> - **Hypothesis:**
> - **Status / measured:** baseline → new (win% + Wilson lb95, n, seeds).

### S0 — Honest, non-mirror evaluation harness
- **Provenance:** §1.2 — mirror tournaments hid the real weaknesses; the ladder
  (600) disagreed with our internal #1–2 ranking.
- **Improves:** evaluation validity → Model Score (consistency & robustness are
  *measured*, not assumed).
- **How:** `scripts/exp_gauntlet.py` — our deck vs a **diverse, well-piloted**
  (SearchTeacher) opponent set spanning Water/Fire/Psychic/Lightning/Dragon/control,
  **both seats**, multi-seed, reporting win% + Wilson **lb95**. Hang-proofed
  (`max_steps`, per-chunk timeout). Config-driven so every agent variant is
  compared against the *same fixed gauntlet*.
- **Status:** harness built; baseline measuring (see §3).

### S1 — Develop a bench / stop bricking on a lone basic _(planned)_
- **Provenance:** replay §1.1 — lone basic + empty bench = one KO from losing.
- **Improves:** consistency & robustness (don't depend on a perfect opener) →
  Model Score; better use of Buddy-Buddy Poffin → Deck Score.
- **How (planned):** eval term that values Pokémon-in-play count and heavily
  penalizes being at ≤1 Pokémon (a KO = a loss), so search prioritizes benching
  basics / playing Poffin when the board is thin. Possibly + a deck tweak for
  more reliable early basics.
- **Hypothesis:** fewer turn-1/2 blowout losses, especially going first.
- **Status:** not yet implemented.

### S2 — Hand-size discipline vs Resentful Refrain _(planned)_
- **Provenance:** replay §1.1 — 8-card hand → 400-dmg Refrain.
- **Improves:** robustness vs the mirror's win condition → Model Score.
- **How (planned):** give the 2-ply rollout a **realistic opponent model** (a
  meta deck that can evolve Froslass and Refrain) so the search *sees* the threat
  of a fat hand and over-extension, ± an explicit hand-size penalty when an
  opposing Refrain attacker is in play.
- **Hypothesis:** smaller end-of-turn hands vs Froslass; better going-first mirror.
- **Status:** not yet implemented.

### S3 — Spend the time budget: deeper search _(planned)_
- **Provenance:** we use ~2–3 s/game of a large per-game budget (replay
  `remainingOverageTime` ≈ 600, barely moved). Massive unused headroom.
- **Improves:** tactical strength & consistency → Model Score.
- **How (planned):** extend beyond 2-ply and/or average more determinization
  samples, under a safe `time_budget`.
- **Hypothesis:** higher win% vs strong peers.
- **Status:** not yet implemented.

---

## 3. Measurements

_Filled in as runs complete. Each row: agent variant vs the fixed gauntlet,
both seats, n games/opponent, multi-seed, win% with Wilson lb95._

### 3.1 vs strong peer `mega_starmie_ex` (piloted plies=2, both seats)

**⚠ Methodology correction (the headline lesson).** An early n=200 comparison
suggested the `develop` eval terms gave +5pt (45%→50%). A larger **n=500** rerun
**reversed it** — the +5pt was unseeded-RNG noise. Independent adversarial review
(2 reviewers) confirmed: the engine RNG lives in the compiled `cg` lib with no
Python seeding, so every point is a noisy sample; n=200 swings ±7pt.

| Variant | win% | lb95 | n | verdict |
|---|---|---|---|---|
| **baseline (`plies=2, dynamic_attack`)** | **51.0%** | 46.6% | **500** | **best agent config — kept** |
| `develop` (+bench +fragility penalty) | 47.4% | 43.1% | 500 | rejected (noise/slightly worse) |
| `dev_f1000` (fragility=1000) | 45.3% | 39.8% | 300 | rejected (worse) |
| `develop` (early) | 50.0% | 43.1% | 200 | ⚠ noise — not reproduced |
| `develop3` (depth-3) | 46.5% | 39.7% | 200 | rejected (rollout errors compound) |
| consistency deck `2c` (−2 Energy Search +2 Ultra Ball) | 41.5% | 34.9% | 200 | rejected (hurt) |

**Takeaway (Model Score → soundness & robustness):** the agent is **already ~even
(≈51%) vs a strong peer**; eval-term tweaks, deeper search, and the one deck edit
tried all failed to beat it at honest sample sizes. Why the eval terms didn't bite:
the new terms only affect *single-choice* (`_learnable`) decisions, but benching is
usually a forced/multi-select setup decision delegated to the heuristic — so they
couldn't steer board development. **The lever is the DECK** (re-confirms the project
thesis), pursued via the high-n autonomous search in §5. All future config/deck
decisions use **n≥500** and a **multi-deck** gauntlet (anti-over-fit).

### 3.2 Intrinsic robustness (self-mirror, n=80)
| Metric | baseline | target |
|---|---|---|
| never-benched (lone attacker all game) | 15.0% | ↓ |
| fragile (≤1 Pokémon in play at an end-of-turn after T1) | 41.9% | ↓ |
| avg end-of-turn hand (Refrain = 50× this) | 4.30 | ↓ |

_(to be re-measured on the winning config)_

---

### S4 — Autonomous high-n deck+config search (the main thrust)
- **Provenance:** §3.1 — the agent is already ~even vs the strong peer and eval-term
  tweaks failed at honest n; the project thesis + replay both point to the **deck**.
- **Improves:** the deck itself (Deck Score) + measured robustness across a diverse
  opponent set (Model Score), with a fully auditable search trail (Report Score).
- **How:** `scripts/opt_loop.py` maintains a CHAMPION and tests CHALLENGERS vs a
  4-deck strongly-piloted gauntlet (`mega_starmie_ex` peer, `starmie_aggro_tuned`,
  `lightning_counter`, `dragapult_ex_meta`) at **n=600/challenger**, promoting only
  on a Wilson **lb95** guard (no noise-chasing). Challengers come from (1) LLM
  analysts — `scripts/gen_challengers_llm.py` queries **OpenAI gpt-4o + Anthropic
  sonnet + Sakana fugu** (Grok = no credits) for legal card-swap proposals with
  rationale, which are *measured, not trusted*; (2) systematic single-card swaps.
- **Hypothesis:** a consistency-oriented deck edit (e.g., a draw/search basic to cut
  turn-1 bricks) reliably beats the current list across the gauntlet.
- **Status:** **running** 11:53→16:25 (2026-06-25). Champion start = baseline
  `mega_starmie_ex_2` @ 76.8% aggregate (lb95 73.3%, n=600). Live log:
  `data/opt/log.md`; champion: `data/opt/champion.json`; trail: `data/opt/history.jsonl`.

### Strategy outcomes so far (measured, honest)
| Strategy | Outcome |
|---|---|
| S1 bench/fragility eval terms | **rejected** — 47.4% ≤ baseline 51.0% @ n=500 (terms can't steer forced/multi-select bench decisions) |
| S2 hand-discipline penalty | **rejected** — 44.5% @ n=200, no help, often inert |
| S3 deeper search (3-ply) | **rejected** — 46.5%, rollout errors compound |
| deck `2c` (Ultra Ball for Energy Search) | **rejected** — 41.5%, hurt |
| S4 autonomous high-n deck/LLM search | **running** |

## 4. Figures (planned)
- Fig 1: replay `81844919` loss timeline (lone basic → fat hand → Refrain 400 → loss).
- Fig 2: win% by variant vs gauntlet (bar chart, lb95 error bars).
- Fig 3: intrinsic metrics before/after (brick rate, avg end-of-turn hand size, win% by seat).
