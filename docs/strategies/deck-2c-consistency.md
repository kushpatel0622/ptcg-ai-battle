# deck `mega_starmie_ex_2c` — Ultra Ball consistency variant

- **Provenance:** [replay](replay-81844919-analysis.md) — lone-basic bricks; the pool
  has **Ultra Ball (id 1121)** which fetches *any* Pokémon AND discards 2 (shrinking
  the hand vs Resentful Refrain). Plausibly fixes both problems at once.
- **Improves:** turn-1 consistency + hand discipline → **Deck Score**.
- **How:** `decks/mega_starmie_ex_2c.csv` = champion deck **−2 Energy Search (1119),
  +2 Ultra Ball (1121)**. Validated legal (60 cards, ≤4, starts a battle).
- **Hypothesis:** more Pokémon-search + smaller hand → fewer bricks → higher win%.
- **Measured (develop config vs strong peer, n=200):** **41.5%** — clearly *worse*
  than the original deck.
- **Verdict:** **REJECTED.** Cutting Energy Search hurt the Water deck's energy
  consistency, and Ultra Ball's discard-2 cost tempo/cards against a fast peer. The
  "more search = better" intuition lost to the simulator.
- **Rubric:** Deck Score (a measured deck hypothesis; documents why a sensible-looking
  edit was wrong — the kind of rigor that avoids shipping a worse list).
