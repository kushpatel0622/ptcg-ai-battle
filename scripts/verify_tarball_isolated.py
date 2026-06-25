"""Gold-standard submission check: run the agent from an EXTRACTED copy of
submission.tar.gz, with numpy/torch/engine/baselines/rl import-blocked, playing
full self-games via cg directly (no engine.harness import).

Proves the tarball is self-contained + numpy-free + runs error-free, and reports
per-game total thinking time (the cabt budget is ~12 s of thinking PER GAME).

Usage:  python scripts/verify_tarball_isolated.py [n_games]
Run with the conda python; it extracts to a temp dir and imports only from there.
"""
import importlib.abc
import importlib.machinery
import os
import sys
import tarfile
import tempfile
from time import perf_counter

N_GAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 6
BLOCKED = {"numpy", "torch", "engine", "baselines", "rl", "llm"}


class _Blocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        top = fullname.split(".")[0]
        if top in BLOCKED:
            raise ImportError(f"BLOCKED import '{fullname}' (must be self-contained)")
        return None


def main():
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tar = os.path.join(repo, "submission.tar.gz")
    if not os.path.exists(tar):
        sys.exit(f"missing {tar}")

    tmp = tempfile.mkdtemp(prefix="iso_sub_")
    with tarfile.open(tar) as tf:
        tf.extractall(tmp)
    print(f"extracted tarball -> {tmp}")
    print("contents:", sorted(os.listdir(tmp)))

    # Isolate: ONLY the extracted dir is importable (+ stdlib). Block the libs.
    sys.meta_path.insert(0, _Blocker())
    sys.path.insert(0, tmp)
    os.chdir(tmp)

    import main as agent_mod  # noqa: E402  (the vendored submission main.py)
    from cg.api import LogType, to_observation_class  # noqa: E402
    from cg.game import battle_finish, battle_select, battle_start  # noqa: E402

    # Deck the agent selects = what main.py would return on obs.select is None.
    deck = agent_mod.DECK
    assert len(deck) == 60, f"deck len {len(deck)}"
    agent = agent_mod.agent

    def play_one():
        obs_dict, start = battle_start(deck, deck)
        if obs_dict is None:
            raise RuntimeError(f"battle_start failed type={start.errorType}")
        result, turns, decisions, think = -1, 0, 0, 0.0
        try:
            for _ in range(100_000):
                obs = to_observation_class(obs_dict)
                for lg in obs.logs:
                    if lg.type == LogType.RESULT:
                        result = lg.result
                if obs.current is not None:
                    turns = obs.current.turn
                    if obs.current.result != -1:
                        result = obs.current.result
                        break
                if obs.select is None:
                    break
                t0 = perf_counter()
                action = list(agent(obs_dict))
                think += perf_counter() - t0
                decisions += 1
                obs_dict = battle_select(action)
            else:
                raise RuntimeError("did not terminate")
        finally:
            battle_finish()
        return result, turns, decisions, think

    errors, times = 0, []
    for g in range(N_GAMES):
        try:
            res, turns, dec, think = play_one()
            times.append(think)
            print(f"game {g}: result={res} turns={turns} decisions={dec} "
                  f"think={think:.2f}s")
        except Exception as e:
            errors += 1
            print(f"game {g}: ERROR {type(e).__name__}: {e}")

    print("\n=== SUMMARY ===")
    print(f"games={N_GAMES} errors={errors}")
    if times:
        print(f"think/game  max={max(times):.2f}s  mean={sum(times)/len(times):.2f}s")
        print(f"budget=~12s/game  ->  margin {12/max(times):.1f}x at worst case")
    print("numpy loaded?", "numpy" in sys.modules, "| torch loaded?", "torch" in sys.modules)
    print("RESULT:", "PASS" if errors == 0 else "FAIL")


if __name__ == "__main__":
    main()
