"""Learning stack: replay ingestion, model, datasets, behavior cloning, PPO.

Importing this package makes the bundled engine importable (puts submission/ on
sys.path), like the other training-side packages.
"""
import engine  # noqa: F401  (puts submission/ on sys.path so `cg` imports)
