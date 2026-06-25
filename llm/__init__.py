"""LLM teacher fleet: pluggable LLM-backed agents that play the TCG, an arena to
league them, and serialization that turns the engine observation into a prompt.

The submitted ladder agent is NOT an LLM (no internet in the grader) — this
package generates offline games/reasoning that get distilled into the neural
policy (see rl/).
"""
import engine  # noqa: F401  (puts submission/ on sys.path so `cg` imports)
