from __future__ import annotations

import json
from typing import Dict, Any

from opentelemetry import trace
from langfuse import observe

from generated.contracts.v1 import contracts_pb2 as pb

tracer = trace.get_tracer(__name__)  # type: ignore[attr-defined]


def _score_patch(diff: str) -> float:
    """Simple heuristic scoring for a patch diff."""
    return 0.9 if "assert True" in diff else 0.5


from utils import validate_envelope


def _validate_critique(critique: pb.Critique) -> None:  # type: ignore[name-defined]
    envelope = {
        "context": {},
        "payload": {"score": critique.score, "feedback": critique.feedback},
        "tool_calls": [],
    }
    validate_envelope(envelope, "critique")


@observe()
def critic_node(state: Dict[str, Any]) -> Dict[str, Any]:
    with tracer.start_as_current_span("critic_agent"):
        patch: pb.Patch = state["patch"]  # type: ignore[name-defined]
        score = _score_patch(patch.diff)
        feedback = "looks good" if score >= 0.8 else "needs work"
        critique = pb.Critique(score=score, feedback=feedback)  # type: ignore[attr-defined]
        _validate_critique(critique)
        return {"critique": critique}
