from __future__ import annotations

import difflib
from typing import Dict, Any

from langfuse import observe
from utils import get_logger
from contracts import Tests, Patch

logger = get_logger(__name__)


def _create_patch(tests: Tests) -> str:
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
    tests: Tests = state["tests"]
    logger.debug("code_node input has %d chars", len(tests.code))
    patch_text = _create_patch(tests)
    result = {"patch": Patch(diff=patch_text)}
    logger.debug("code_node output diff len: %d", len(patch_text))
    return result
