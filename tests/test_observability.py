from pathlib import Path

import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from nodes import spec_agent, tests_agent, code_agent, critic_agent


def test_nodes_have_observe_wrapper():
    for fn in [
        spec_agent.spec_node,
        tests_agent.test_node,
        code_agent.code_node,
        critic_agent.critic_node,
    ]:
        assert hasattr(fn, "__wrapped__"), f"{fn.__name__} missing observe decorator"
