from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langfuse import observe
from utils import get_logger
from generated.contracts.v1 import contracts_pb2 as pb
from nodes.spec_agent import spec_node
from nodes.tests_agent import test_node
from nodes.code_agent import code_node
from nodes.critic_agent import critic_node

logger = get_logger(__name__)


class WorkflowState(TypedDict, total=False):
    feature_request: pb.FeatureRequest  # type: ignore[name-defined]
    spec: pb.Spec  # type: ignore[name-defined]
    tests: pb.Tests  # type: ignore[name-defined]
    patch: pb.Patch  # type: ignore[name-defined]
    critique: pb.Critique  # type: ignore[name-defined]
    repair_plan: pb.RepairPlan  # type: ignore[name-defined]
    attempts: int


# --- Node implementations -------------------------------------------------


@observe()
def repair_node(state: WorkflowState) -> dict:
    attempt = state.get("attempts", 0) + 1
    logger.debug("repair_node attempt %d", attempt)
    result = {
        "repair_plan": pb.RepairPlan(steps=[f"fix {attempt}"]),  # type: ignore[attr-defined]
        "attempts": attempt,
    }
    logger.debug("repair_node output: %s", result)
    return result


# --- Routers ---------------------------------------------------------------


def route_after_critic(state: WorkflowState):
    if state["critique"].score >= 0.8:
        return END
    return "repair"


def route_after_repair(state: WorkflowState):
    if state.get("attempts", 0) >= 3:
        return END
    return "code"


# --- Graph builder ---------------------------------------------------------


def create_graph() -> CompiledStateGraph:
    logger.debug("create_graph")
    builder = StateGraph(WorkflowState)
    builder.add_node("spec", spec_node)  # type: ignore[arg-type,call-overload]
    builder.add_node("tests", test_node)  # type: ignore[arg-type,call-overload]
    builder.add_node("code", code_node)  # type: ignore[arg-type,call-overload]
    builder.add_node("critic", critic_node)  # type: ignore[arg-type,call-overload]
    builder.add_node("repair", repair_node)  # type: ignore[arg-type,call-overload]

    builder.add_edge(START, "spec")
    builder.add_edge("spec", "tests")
    builder.add_edge("tests", "code")
    builder.add_edge("code", "critic")

    builder.add_conditional_edges("critic", route_after_critic)
    builder.add_conditional_edges("repair", route_after_repair)

    compiled = builder.compile()
    logger.debug("graph compiled")
    return compiled


# default compiled graph
graph = create_graph()
