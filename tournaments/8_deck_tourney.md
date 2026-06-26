# 8-Deck Round-Robin Tournament (re-run, aggressive combo configs)

_200 games/pair, 8 decks, 28 matchups. Combo decks now piloted with `w_dmg=10` (aggressive: uses Phantom Dive / the big toolbox attacks more)._

## Roster

| # | deck | archetype | config | vs heuristic |
|---|------|-----------|--------|--------------|
| 1 | `fighting_pivot` | Fighting / Mega Lucario ex aggro-toolbox | 2-ply | 85.4% |
| 2 | `single_prize_control` | Water Walrein single-prize control | 2-ply | 86.5% |
| 3 | `mega_starmie_ex_2` | Water dual Mega (Starmie + Froslass) ex | 2-ply | 80.1% |
| 4 | `starmie_aggro` | Water Mega Starmie ex pure aggro | 2-ply | 78.9% |
| 5 | `dragapult_dusknoir` | Dragapult ex / Dusknoir spread-combo | 2-ply aggr | 88.1% |
| 6 | `ns_zoroark_toolbox` | N's Zoroark ex Darkness toolbox | 2-ply aggr | 86.1% |
| 7 | `lightning_counter` | Lightning anti-Water tech | 2-ply | 75.4% |
| 8 | `mega_starmie_ex` | Water pure Mega Starmie ex aggro (dominant replay/meta deck) | 1-ply | 71.2% |

## Win-rate matrix (row's win% vs column)

| vs → | fighting pivo | single prize  | mega starmie  | starmie aggro | dragapult dus | ns zoroark to | lightning cou | mega starmie  |
|------|---|---|---|---|---|---|---|---|
| **fighting pivo** |  —  | 56% | 11% | 40% | 69% | 74% | 92% | 11% |
| **single prize ** | 44% |  —  | 21% | 26% | 63% | 61% | 48% | 8% |
| **mega starmie ** | 89% | 79% |  —  | 76% | 93% | 88% | 90% | 46% |
| **starmie aggro** | 60% | 74% | 24% |  —  | 80% | 72% | 66% | 20% |
| **dragapult dus** | 31% | 37% | 7% | 20% |  —  | 57% | 49% | 4% |
| **ns zoroark to** | 26% | 39% | 12% | 28% | 43% |  —  | 50% | 12% |
| **lightning cou** | 8% | 52% | 10% | 34% | 51% | 50% |  —  | 16% |
| **mega starmie ** | 89% | 92% | 54% | 80% | 96% | 88% | 84% |  —  |

## Overall ranking (vs the field)
| rank | deck | win% | record |
|------|------|------|--------|
| 1 | `mega_starmie_ex` | **83.3%** | 1165/1399 |
| 2 | `mega_starmie_ex_2` | **80.2%** | 1121/1398 |
| 3 | `starmie_aggro` | **56.4%** | 790/1400 |
| 4 | `fighting_pivot` | **50.5%** | 707/1400 |
| 5 | `single_prize_control` | **38.8%** | 542/1396 |
| 6 | `lightning_counter` | **31.5%** | 441/1398 |
| 7 | `ns_zoroark_toolbox` | **30.1%** | 421/1399 |
| 8 | `dragapult_dusknoir` | **29.1%** | 406/1396 |

## Per-deck strategy

### mega_starmie_ex — Water pure Mega Starmie ex aggro (dominant replay/meta deck)
_Field: **83.3%** · 71.2% vs heuristic_

The most-played ladder deck — blazing fast but inconsistent: only 3 true basics (Staryu) plus 4 unplayable line-less Cinderace, so it bricks often. Best at 1-ply (2-ply's extra rollout adds noise on a deck that bricks).

### mega_starmie_ex_2 — Water dual Mega (Starmie + Froslass) ex
_Field: **80.2%** · 80.1% vs heuristic_

Two 1-energy Mega ex attackers: Mega Starmie ex (Jetting Blow 120 + 50 bench snipe / Nebula Beam 210 ignores effects) and Mega Froslass ex (Resentful Refrain = 50× opponent hand size, invisible to the heuristic). 8 basics for consistency — a fast, flexible 1-energy tempo deck.

### starmie_aggro — Water Mega Starmie ex pure aggro
_Field: **56.4%** · 78.9% vs heuristic_

4 Mega Starmie ex + 4 Budew: the fastest 1-energy clock, with Budew slowing the opponent's Item-based setup. A glass-cannon prize race.

### fighting_pivot — Fighting / Mega Lucario ex aggro-toolbox
_Field: **50.5%** · 85.4% vs heuristic_

Mega Lucario ex (340 HP, Mega-evolves from Riolu) is a one-Prize-efficient beater; Flygon ex / Fezandipiti ex / Meowth ex add dynamic-damage attacks (Cruel Arrow = 100 snipe to any Pokémon, Sonic Peridot = 100 to each opposing ex) that the heuristic scores as 0 and never plays. 33-card trainer engine. Wins by relentless efficient attacks plus picking off key targets; the dynamic_attack fix makes it our strongest deck vs the heuristic.

### single_prize_control — Water Walrein single-prize control
_Field: **38.8%** · 86.5% vs heuristic_

Spheal→Sealeo→Walrein walls (single-Prize attackers, so the opponent must score six KOs while we trade up) backed by Dunsparce/Dudunsparce draw. Grinds the game out; 2-ply's defensive read — keep the wall alive to attack again — is decisive.

### lightning_counter — Lightning anti-Water tech
_Field: **31.5%** · 75.4% vs heuristic_

Pikachu ex + Mega Manectric ex (330 HP) with Eelektrik energy acceleration, exploiting the Water-heavy meta's Lightning weakness. Slower to set up (heavy energy + evolution lines), so it is our lowest non-brick deck.

### ns_zoroark_toolbox — N's Zoroark ex Darkness toolbox
_Field: **30.1%** · 86.1% vs heuristic_

N's Zorua→N's Zoroark ex (Trade = discard 1/draw 2; Night Joker = copy a benched N's attack) powers a toolbox — N's Darmanitan snipe (Back Draft 30× opp energy), N's Reshiram / Zekrom, and Bloodmoon Ursaluna ex (Blood Moon 240) — off mono-Darkness energy. Munkidori damage-move, Pecharunt ex + Air Balloon + N's Castle mobility, Judge disruption. 1-Prize attackers force bad trades. Heavily combo-dependent (Night Joker is the whole attack engine).

### dragapult_dusknoir — Dragapult ex / Dusknoir spread-combo
_Field: **29.1%** · 88.1% vs heuristic_

Dreepy→Drakloak (Recon Directive draw)→Dragapult ex (Phantom Dive 200 + 6-counter bench spread) with the Dusclops/Dusknoir Cursed Blast engine (place 13 counters, self-KO) and Munkidori (Adrena-Brain damage-move) to hit exact KO math. Rare Candy for Stage-2 speed; Judge/Unfair Stamp disruption. A Stage-2 COMBO that the search plays tactically (immediate damage) more than as the multi-turn spread/prize-race the deck is built for.
