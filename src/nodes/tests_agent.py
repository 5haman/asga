from __future__ import annotations

import os
import random
import textwrap
from typing import Dict, Any

from langfuse import observe
from utils import get_logger
from generated.contracts.v1 import contracts_pb2 as pb

logger = get_logger(__name__)


SEED = int(os.getenv("OPENROUTER_SEED", "42"))


def _generate_tests(spec: pb.Spec) -> str:  # type: ignore[name-defined]
    rnd = random.Random(SEED)
    name = spec.endpoint.strip("/").replace("/", "_") or "root"
    test_id = rnd.randint(0, 9999)
    code = f"""import pytest


def test_{spec.method.lower()}_{name}_{test_id}():
    assert False, \"not implemented\"
"""
    return textwrap.dedent(code)


def _validate_tests(code: str) -> None:
    compile(code, "<generated>", "exec")


@observe()
def test_node(state: Dict[str, Any]) -> Dict[str, Any]:
    spec: pb.Spec = state["spec"]  # type: ignore[name-defined]
    logger.debug("test_node input endpoint: %s", spec.endpoint)
    code = _generate_tests(spec)
    _validate_tests(code)
    result = {"tests": pb.Tests(code=code)}  # type: ignore[attr-defined]
    logger.debug("test_node output length: %d", len(code))
    return result
