import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from generated.contracts.v1 import contracts_pb2 as pb
from nodes import tests_agent as test_agent


def _write(code: str, path: Path) -> Path:
    path.write_text(code)
    return path


def test_compilation(tmp_path):
    spec = pb.Spec(endpoint="/demo", method="GET", request_schema="{}", response_schema="{}")
    res = test_agent.test_node({"spec": spec})
    test_file = _write(res["tests"].code, tmp_path / "test_generated.py")
    out = subprocess.run(["pytest", "--collect-only", str(test_file)], capture_output=True)
    assert out.returncode == 0


def test_determinism(monkeypatch):
    monkeypatch.setenv("OPENROUTER_SEED", "123")
    spec = pb.Spec(endpoint="/demo", method="GET", request_schema="{}", response_schema="{}")
    res1 = test_agent.test_node({"spec": spec})
    res2 = test_agent.test_node({"spec": spec})
    h1 = hashlib.sha256(res1["tests"].code.encode()).hexdigest()
    h2 = hashlib.sha256(res2["tests"].code.encode()).hexdigest()
    assert h1 == h2


def test_failure(tmp_path):
    spec = pb.Spec(endpoint="/demo", method="GET", request_schema="{}", response_schema="{}")
    res = test_agent.test_node({"spec": spec})
    test_file = _write(res["tests"].code, tmp_path / "test_fail.py")
    out = subprocess.run(["pytest", str(test_file)], capture_output=True)
    assert out.returncode != 0
