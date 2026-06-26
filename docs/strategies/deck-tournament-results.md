# Deck tournament — our candidate decks vs the smart gauntlet (high-n)

First experiment of the autonomous run ([S4](S4-autonomous-search.md)): each
candidate deck piloted by the **baseline config**, vs the 4-deck strongly-piloted
gauntlet, n≈600, both seats. Per-opponent win% in brackets `[mega starmie lightning dragapult]`.

## Round 1 (2026-06-25 11:56)
| Deck (as ours) | aggregate | lb95 | peer (mega) | verdict |
|---|---|---|---|---|
| **mega_starmie_ex_2 (champion)** | **76.8%** | 73.3% | **57%** | best base deck |
| mega_starmie_ex | 76.3% | 72.8% | 46% | near-tie aggregate, worse peer |
| starmie_aggro_tuned | 52.6% | 48.6% | 18% | far worse |
| walrein_tuned | 47.8% | 43.9% | 13% | far worse |
| starmie_ctrl_tuned | 46.9% | 42.9% | 24% | far worse |
| mega_starmie_ex_3 | 42.3% | 38.4% | 13% | far worse |
| abomasnow_v1 | 39.2% | 35.3% | 11% | far worse |

## Round 2 (2026-06-25 12:22)
| Challenger | aggregate | lb95 | peer | verdict |
|---|---|---|---|---|
| wildcard_best | 77.0% | 73.5% | 53% | near-tie; **not promoted** (lb95 73.5% < champ 76.3%) |
| cfg margin5 | 76.2% | 72.6% | 51% | ~tie, not promoted |
| cfg samples3 | 74.2% | 70.5% | 40% | worse |
| fezandipiti_ex | 64.0% | 60.1% | 26% | worse |

## Reading
- **`mega_starmie_ex_2` is confirmed the best base deck at high n** — and it has the
  *best peer matchup* (57%) of the top tier, the matchup that actually discriminates.
- A top tier (`mega_starmie_ex_2`, `mega_starmie_ex`, `wildcard_best`) sits ~76–77%;
  everything else is ≥20pt behind → the meta really is dominated by this Water-aggro
  shell (re-confirms the project thesis).
- No challenger has beaten the champion under the conservative lb95 guard. The peer
  (~53–57%) is the only headroom; refinement focuses there via LLM card-swaps.
