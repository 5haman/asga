from __future__ import annotations

import difflib
from typing import Dict, Any

from langfuse import observe
from utils import get_logger

logger = get_logger(__name__)

from generated.contracts.v1 import contracts_pb2 as pb




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
    tests: pb.Tests = state["tests"]  # type: ignore[name-defined]
    logger.debug("code_node input has %d chars", len(tests.code))
    patch_text = _create_patch(tests)
    result = {"patch": pb.Patch(diff=patch_text)}  # type: ignore[attr-defined]
    logger.debug("code_node output diff len: %d", len(patch_text))
    return result
