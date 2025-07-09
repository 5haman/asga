from __future__ import annotations

from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from opentelemetry import trace
from opentelemetry.trace import Tracer
from langfuse import observe

from generated.contracts.v1 import contracts_pb2 as pb
from nodes.spec_agent import spec_node
from nodes.tests_agent import test_node
from nodes.code_agent import code_node
from nodes.critic_agent import critic_node

tracer: Tracer = trace.get_tracer(__name__)  # type: ignore[attr-defined]


@observe()
def optimise_simba(state: WorkflowState) -> dict:
    """SIMBA optimisation loop triggered on failed critique."""
    with tracer.start_as_current_span("optimise_simba"):
        attempt = state.get("attempts", 0) + 1
        return {
            "repair_plan": pb.RepairPlan(steps=[f"fix {attempt}"]),  # type: ignore[attr-defined]
            "attempts": attempt,
        }


# Backwards compatibility name
repair_node = optimise_simba


class WorkflowState(TypedDict, total=False):
    feature_request: pb.FeatureRequest  # type: ignore[name-defined]
    spec: pb.Spec  # type: ignore[name-defined]
    tests: pb.Tests  # type: ignore[name-defined]
    patch: pb.Patch  # type: ignore[name-defined]
    critique: pb.Critique  # type: ignore[name-defined]
    repair_plan: pb.RepairPlan  # type: ignore[name-defined]
    attempts: int


# --- Node implementations -------------------------------------------------


# --- Routers ---------------------------------------------------------------


def route_after_critic(state: WorkflowState):
    if state["critique"].score >= 0.8:
        return END
    return "optimise"


def route_after_optimise(state: WorkflowState):
    if state.get("attempts", 0) >= 3:
        return END
    return "code"


# --- Graph builder ---------------------------------------------------------


def create_graph() -> CompiledStateGraph:
    builder = StateGraph(WorkflowState)
    builder.add_node("spec", spec_node)  # type: ignore[arg-type,call-overload]
    builder.add_node("tests", test_node)  # type: ignore[arg-type,call-overload]
    builder.add_node("code", code_node)  # type: ignore[arg-type,call-overload]
    builder.add_node("critic", critic_node)  # type: ignore[arg-type,call-overload]
    builder.add_node("optimise", optimise_simba)  # type: ignore[arg-type,call-overload]

    builder.add_edge(START, "spec")
    builder.add_edge("spec", "tests")
    builder.add_edge("tests", "code")
    builder.add_edge("code", "critic")

    builder.add_conditional_edges("critic", route_after_critic)
    builder.add_conditional_edges("optimise", route_after_optimise)

    return builder.compile()


# default compiled graph
graph = create_graph()
