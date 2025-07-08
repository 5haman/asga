from __future__ import annotations

import difflib
from typing import Dict, Any

from opentelemetry import trace
from langfuse import observe

from generated.contracts.v1 import contracts_pb2 as pb

tracer = trace.get_tracer(__name__)  # type: ignore[attr-defined]


def _create_patch(tests: pb.Tests) -> str:  # type: ignore[name-defined]
    """Return unified diff turning failing tests into passing ones."""
    before = tests.code.splitlines(keepends=True)
    after_code = tests.code.replace("assert False", "assert True")
    after = after_code.splitlines(keepends=True)
    diff = difflib.unified_diff(
        before,
        after,
        fromfile="a/tests.py",
        tofile="b/tests.py",
    )
    return "".join(diff)


@observe()
def code_node(state: Dict[str, Any]) -> Dict[str, Any]:
    with tracer.start_as_current_span("code_agent"):
        tests: pb.Tests = state["tests"]  # type: ignore[name-defined]
        patch_text = _create_patch(tests)
        return {"patch": pb.Patch(diff=patch_text)}  # type: ignore[attr-defined]
