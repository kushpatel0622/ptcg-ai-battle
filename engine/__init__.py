"""Training-side helpers around the cabt engine.

Importing this package makes the bundled engine (``submission/cg``) importable
by inserting the submission directory onto ``sys.path``. The engine is pure
ctypes (loads ``cg.dll`` / ``libcg.so``), so it works under any CPython without
conda or pytorch.
"""
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SUBMISSION = os.path.join(_REPO, "submission")
if _SUBMISSION not in sys.path:
    sys.path.insert(0, _SUBMISSION)

REPO_ROOT = _REPO
SUBMISSION_DIR = _SUBMISSION
