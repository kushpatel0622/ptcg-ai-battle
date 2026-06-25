"""Reproducible builder for submission.tar.gz (cabt: Pokemon TCG AI Battle).

Packages submission/ into a clean top-level tarball and ENFORCES the invariants
that make it a valid submission, so the artifact can never silently drift:

  * deck.csv == the DECK hardcoded in main.py, and both are exactly 60 cards;
  * the active agent modules import nothing outside cg/ + the Python stdlib
    (no numpy / torch / engine / baselines / rl) — i.e. self-contained;
  * __pycache__ / *.pyc never get bundled.

Members are written at the TOP level (./main.py, ./cg/api.py, ...), which is the
layout the grader expects. Stdlib only — runs under any Python.

Usage:  python scripts/build_submission.py
Then verify the artifact end-to-end:  python scripts/verify_tarball_isolated.py
"""
import ast
import os
import re
import sys
import tarfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUB = os.path.join(REPO, "submission")
OUT = os.path.join(REPO, "submission.tar.gz")

# Modules that ship as the agent's brain (everything except the cg/ engine).
ACTIVE_MODULES = ["main.py", "search_teacher.py", "heuristic_agent.py",
                  "cards.py", "deck_io.py"]
FORBIDDEN_IMPORT = re.compile(
    r"^\s*(?:import|from)\s+(numpy|torch|engine|baselines|rl|llm)\b", re.M)


def fail(msg):
    sys.exit(f"BUILD FAILED: {msg}")


def deck_from_main():
    src = open(os.path.join(SUB, "main.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "DECK":
                    return list(ast.literal_eval(node.value))
    fail("could not find a top-level `DECK = [...]` in main.py")


def deck_from_csv():
    txt = open(os.path.join(SUB, "deck.csv"), encoding="utf-8").read()
    return [int(x) for x in txt.split() if x.strip()]


def check_invariants():
    # 1) deck consistency + legality (length; full rules are enforced by the
    #    engine's battle_start, exercised by verify_tarball_isolated.py).
    d_main, d_csv = deck_from_main(), deck_from_csv()
    if len(d_main) != 60:
        fail(f"main.py DECK has {len(d_main)} cards, need 60")
    if len(d_csv) != 60:
        fail(f"deck.csv has {len(d_csv)} cards, need 60")
    if d_main != d_csv:
        fail("main.py DECK != deck.csv (keep them identical)")
    for cid, k in {c: d_main.count(c) for c in set(d_main)}.items():
        if cid > 100 and k > 4:                  # basic energy (low ids) exempt
            fail(f"card {cid} appears {k}x (>4 of a non-basic-energy card)")
    print(f"  deck OK: 60 cards, main.py == deck.csv ({len(set(d_main))} distinct)")

    # 2) self-containment: no forbidden top-level imports in the active modules.
    for m in ACTIVE_MODULES:
        src = open(os.path.join(SUB, m), encoding="utf-8").read()
        hit = FORBIDDEN_IMPORT.search(src)
        if hit:
            fail(f"{m} imports forbidden module '{hit.group(1)}' "
                 f"(must be self-contained)")
    print(f"  imports OK: {len(ACTIVE_MODULES)} active modules clean "
          f"(no numpy/torch/engine/baselines/rl)")


def collect_members():
    members = []
    for root, dirs, files in os.walk(SUB):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".pyc"):
                continue
            full = os.path.join(root, f)
            arc = "./" + os.path.relpath(full, SUB).replace(os.sep, "/")
            members.append((full, arc))
    members.sort(key=lambda m: m[1])
    return members


def main():
    if not os.path.isdir(SUB):
        fail(f"no submission dir at {SUB}")
    print("checking invariants...")
    check_invariants()

    members = collect_members()
    needed = {"./main.py", "./deck.csv", "./cg/api.py"}
    have = {a for _, a in members}
    missing = needed - have
    if missing:
        fail(f"missing required members: {sorted(missing)}")

    if os.path.exists(OUT):
        os.remove(OUT)
    with tarfile.open(OUT, "w:gz") as tf:
        for full, arc in members:
            tf.add(full, arcname=arc)

    print(f"\nwrote {OUT} ({os.path.getsize(OUT)} bytes)")
    print("contents:")
    for _, arc in members:
        print(f"  {arc}")
    print("\nOK. Now run:  python scripts/verify_tarball_isolated.py")


if __name__ == "__main__":
    main()
