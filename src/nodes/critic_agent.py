from __future__ import annotations

from typing import Dict, Any

from langfuse import observe
from utils import get_logger, validate_envelope
from contracts import Patch, Critique

logger = get_logger(__name__)


def _score_patch(diff: str) -> float:
    """Simple heuristic scoring for a patch diff."""
    return 0.9 if "assert True" in diff else 0.5


def _validate_critique(critique: Critique) -> None:
    envelope = {
        "context": {},
        "payload": {"score": critique.score, "feedback": critique.feedback},
        "tool_calls": [],
    }
    validate_envelope(envelope, "critique")


@observe()
def critic_node(state: Dict[str, Any]) -> Dict[str, Any]:
    patch: Patch = state["patch"]
    logger.debug("critic_node diff len: %d", len(patch.diff))
    score = _score_patch(patch.diff)
    feedback = "looks good" if score >= 0.8 else "needs work"
    critique = Critique(score=score, feedback=feedback)
    _validate_critique(critique)
    result = {"critique": critique}
    logger.debug("critic_node score: %.2f", score)
    return result
