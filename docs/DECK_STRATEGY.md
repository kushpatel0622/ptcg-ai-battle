# Deck strategies — candidate pool

How each candidate deck is built, the strategy it executes, and its key cards.
Designed by Claude reasoning + the multi-agent design workflow (engine-validated),
plus the meta decks decoded from the JSON replays. Ranked by the engine deck
tournament (`sims/` — heuristic pilot, every deck vs every deck, 12 games/pair).

For *how we'd derive the top deck from scratch*, see [DECK_DISCOVERY.md](DECK_DISCOVERY.md);
for the card-pool reasoning behind these choices, see [CARD_KNOWLEDGE.md](CARD_KNOWLEDGE.md).

## Tournament ranking (who wins)

| Rank | Deck | Win% | Source | One-line concept |
|---:|------|-----:|--------|------------------|
| 1 | `mega_starmie_ex` | **89%** | replay | Pure Mega Starmie aggro — fast 1-energy attacker, effect-ignoring Nebula Beam |
| 2 | `mega_starmie_ex_2` | 81% | replay | Dual Mega Starmie / Mega Froslass ex |
| 3 | `wildcard_best` | 75% | **designed** | Dual Mega-ex (Starmie + Froslass), 1-energy attackers, fast |
| 4 | `starmie_aggro_tuned` | 57% | **designed** | Mono-Water Starmie aggro, consistency-fixed |
| 5 | `abomasnow_v1` | 52% | designed | Mega Abomasnow ex / Kyogre Water (our first build) |
| 6–11 | `mega_starmie_ex_3`, `starmie_ctrl_tuned`, `walrein`, `walrein_tuned`, `fezandipiti_ex`, `offmeta_archetype` | <50% | mixed | control / single-prize / off-meta |

**Verdict:** the Mega Starmie ex family dominates; our best *designed* deck (`wildcard_best`,
dual Mega-ex) is genuinely competitive at #3. Caveat: this ranking is under a *fixed heuristic
pilot*, so decks that need expert evolution lines (e.g. `starmie_ctrl_tuned`, Fire Cinderace)
are underrated here — they will be re-tested once the neural policy can pilot them.

## Designed decks (Claude / multi-agent workflow)

### `wildcard_best` — Dual Mega-ex aggro  *(best designed, 75%)*
- **Concept:** two Stage-1 Mega-ex attackers that each swing off a **single {W}** — Mega Starmie ex
  [1031] (330 HP) and Mega Froslass ex [861] (310 HP) — for relentless, hard-to-disrupt pressure.
- **Strategy:** evolve a Mega-ex turn 1–2 (Buddy-Buddy Poffin + Mega Signal + Salvatore), attack every
  turn for 1 energy, gust with Boss's Orders to close. Two attackers means a KO on one doesn't stop the clock.
- **Key cards:** Mega Starmie ex [1031] / Staryu [1030]; Mega Froslass ex [861] / Snorunt [860]; Buddy-Buddy
  Poffin, Mega Signal, Salvatore (search/accel); Lillie's Determination (draw); 12 energy.
- **Diagnostics:** avg 14 turns, 70–85% prize-decided, 100% vs random.

### `starmie_aggro_tuned` — Mono-Water Starmie aggro  *(57%)*
- **Concept:** the pure meta plan, with the consistency hole fixed.
- **Strategy:** the original meta list ran only 3 Basics + 4 **un-castable** Cinderace (Stage 2 with no
  line). This build cuts the dead cards, runs 4 Staryu / 3 Mega Starmie ex, adds **Lapras ex** (Basic 220-HP
  Water attacker, Tera) and **Budew** (turn-1 item lock) → **10 Basics** for reliable openings; mono-Water
  19 energy matches every cost. Salvatore is the evolution accelerator (Mega Starmie has no Ability).
- **Diagnostics:** avg 15 turns, **85% prize-decided**, 90% vs random.

### `starmie_ctrl_tuned` — Mega Starmie + Dusknoir/Munkidori control  *(75% prize-decided)*
- **Concept:** Mega Starmie ex beatdown plus a lock/disruption shell.
- **Strategy:** Duskull→Dusclops→Dusknoir (Shadow Bind retreat-lock), Munkidori (move damage counters with
  {D} energy), Budew item-lock, Boss's Orders ×3 + Risky Ruins stadium. 11 Basics for consistency.
- **Key cards:** Mega Starmie ex / Staryu; Dusknoir line; Munkidori [112]; Meowth ex [1071] (on-bench tutor).

### `walrein_tuned` — single-prize Walrein  *(78% prize-decided)*
- **Concept:** a one-prize attacker (Walrein, {W}{W} for 170) that the opponent can't 2-prize, ground out with
  recursion + draw.
- **Strategy:** Spheal + Rare Candy → Walrein; Dunsparce/Dudunsparce draw engine; **Night Stretcher** recycles
  self-KO'd Walreins and energy; **Boss's Orders** added (the original had no gust). Budew item-lock early.

### `offmeta_archetype` — Cinderace ex Fire  *(65% prize-decided)*
- **Concept:** Fire Stage-2 ex (Cinderace ex, Flare Strike 280) exploiting the field's heavy Fire weakness.
- **Strategy:** Scorbunny→Raboot→Cinderace ex with Rare Candy; Cyrano ex-search + Fezandipiti ex draw recovery.
  Pairs with energy recursion to power the cost. (Underrated by the heuristic pilot — needs the full evo line.)

## Meta decks (decoded from the JSON replays)
`mega_starmie_ex` (pure aggro, the tournament champion), `mega_starmie_ex_2` (Starmie/Froslass),
`mega_starmie_ex_3` (Starmie/Dusclops control), `walrein` (single-prize), `fezandipiti_ex` (Alakazam/
Dudunsparce). These are studied for *technique* (energy-denial tempo, evolution acceleration, single-prize
attackers) — which we then transfer to other cards in `CARD_KNOWLEDGE.md`.
