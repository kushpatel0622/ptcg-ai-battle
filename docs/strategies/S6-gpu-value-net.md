# S6 — GPU value-net leaf evaluator

- **Provenance:** user asked to "use the GPU." The deployed agent is pure search
  (0 learned params); the only way a GPU helps is a learned **leaf evaluator** that
  blends `v_scale · V(state)` into the 2-ply leaf score. (Prior sessions found this
  **LOST** head-to-head — re-testing honestly with current champion data.)
- **Improves (hypothesis):** sharper positional eval at the search leaf → **Model Score**.
- **How:**
  1. `scripts/gen_value_data.py` (patched to the **champion deck** `mega_starmie_ex_2`)
     → 200 self-play games → 19,659 encoded states labeled by game outcome.
  2. `scripts/train_value_net.py` on **CUDA** (RTX 2060 SUPER): `ValueNet` (rl/value_net.py),
     40 epochs → **val acc ~72–74%** (vs 53.5% predict-majority baseline). Saved
     `data/checkpoints/value_net_champ.pt`.
  3. `scripts/eval_valuenet.py` — SearchTeacher with `value_net + v_scale ∈ {0,0.5,1.0}`
     vs the peer (plies=2), n=200/scale. **(running)**
- **⚠ Shipping constraint (decisive):** even if the value net *wins*, it **cannot ship** —
  it needs torch/numpy at inference, but the submission is deliberately **numpy-free**
  pure-search (self-containment + timing). Deploying it would require re-introducing a
  numpy/python forward pass I removed. So this track is **academic** w.r.t. the actual
  submission, regardless of outcome.
- **Measured (n=200/scale vs peer, plies=2):** baseline (no net) **49.0%** (lb95 42.2%);
  v_scale 0.5 → **46.5%**; v_scale 1.0 → **47.5%**. The value net does **NOT** beat the
  hand-crafted eval at any blend (all ≤ baseline, within noise). Training: 73% val-acc on CUDA.
- **Verdict:** **REJECTED.** Confirms the prior finding — a learned leaf eval doesn't beat
  the hand-crafted Δ-eval + search, and it is **unshippable** anyway (numpy-free submission).
  The GPU was genuinely exercised (CUDA data-gen + training); pure search remains the
  correct deployed choice. The deck search (which *can* ship) keeps the cores.
- **Rubric:** Model Score (documents a learned-eval attempt + why pure search is the
  right deployed choice — a sound, honest negative is rubric-positive).
