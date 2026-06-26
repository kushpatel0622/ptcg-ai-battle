# Finding — the peer/mirror matchup is a structural ~50% coinflip

After ~30 challengers tested under **peer-primary** fitness (high-n, n=300 on the
peer), a clear, consistent result has emerged:

**Nothing reliably beats baseline `mega_starmie_ex_2` on the peer matchup.** The peer
win% sits at **~46–51% across every round and every edit** (within the n=300 noise
band, ±5.6pt). Tested and all landing at ~44–51% peer (none promoted):
- **Consistency** edits: Ultra Ball, Team Rocket's Great Ball, Arven lines,
  Clefairy/Tadbulb/Ribombee basics — these *regress* the peer (38–46%).
- **Tempo/disruption** edits: +1 Boss's Orders, +1 Mega Signal, Energy Switch,
  Arven's Sandwich, Scramble Switch, Lillie's Pearl — ~44–49%, no confident gain.
- **Config** edits: samples=3, override_margin=5, w_dmg=6 — no gain.
- **GPU** value-net leaf eval — no gain ([S6](S6-gpu-value-net.md)).

## Interpretation
The "peer" (`mega_starmie_ex`) is the same Water Mega-aggro shell as our deck, so the
matchup is a **near-mirror → inherently ~50%**, decided by seat (going second can
evolve+attack first) and opening draws, not by marginal card choices. Within this
meta shell and card pool, `mega_starmie_ex_2` is **at or near the optimum**; the field
(other archetypes) we already beat 80–97%, and they're 20+ pts behind as *our* deck.

## Implication for the 600→1367 ladder gap
This gap is **not closable by deck/config tweaks** in our internal meta — our internal
opponents top out at this Water-aggro shell, which we already mirror at ~50% and beat
elsewhere. The real ladder's stronger/different decks can't be replicated from our
pool. **The defensible competition move is to ship the proven baseline** and report
the rigorous search that confirms it near-optimal, rather than ship a noise-promoted
or peer-regressing edit. (See [DECISIONS.md](DECISIONS.md), [S5](S5-peer-primary-fitness.md).)
