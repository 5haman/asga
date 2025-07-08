from __future__ import annotations

from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from opentelemetry import trace
from opentelemetry.trace import Tracer

from generated.contracts.v1 import contracts_pb2 as pb
from nodes.spec_agent import spec_node

tracer: Tracer = trace.get_tracer(__name__)


class WorkflowState(TypedDict, total=False):
    feature_request: pb.FeatureRequest  # type: ignore[name-defined]
    spec: pb.Spec  # type: ignore[name-defined]
    tests: pb.Tests  # type: ignore[name-defined]
    patch: pb.Patch  # type: ignore[name-defined]
    critique: pb.Critique  # type: ignore[name-defined]
    repair_plan: pb.RepairPlan  # type: ignore[name-defined]
    attempts: int


# --- Node implementations -------------------------------------------------


def test_node(state: WorkflowState) -> dict:
    with tracer.start_as_current_span("test_agent"):
        return {"tests": pb.Tests(code="# tests")}  # type: ignore[attr-defined]


def code_node(state: WorkflowState) -> dict:
    with tracer.start_as_current_span("code_agent"):
        attempt = state.get("attempts", 0)
        return {"patch": pb.Patch(diff=f"diff {attempt}")}  # type: ignore[attr-defined]


def critic_node(state: WorkflowState) -> dict:
    with tracer.start_as_current_span("critic_agent"):
        return {"critique": pb.Critique(score=1.0, feedback="ok")}  # type: ignore[attr-defined]


def repair_node(state: WorkflowState) -> dict:
    with tracer.start_as_current_span("repair_agent"):
        attempt = state.get("attempts", 0) + 1
        return {
            "repair_plan": pb.RepairPlan(steps=[f"fix {attempt}"]),  # type: ignore[attr-defined]
            "attempts": attempt,
        }


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
    builder = StateGraph(WorkflowState)
    builder.add_node("spec", spec_node)  # type: ignore[arg-type,call-overload]
    builder.add_node("tests", test_node)
    builder.add_node("code", code_node)
    builder.add_node("critic", critic_node)
    builder.add_node("repair", repair_node)

    builder.add_edge(START, "spec")
    builder.add_edge("spec", "tests")
    builder.add_edge("tests", "code")
    builder.add_edge("code", "critic")

    builder.add_conditional_edges("critic", route_after_critic)
    builder.add_conditional_edges("repair", route_after_repair)

    return builder.compile()


# default compiled graph
graph = create_graph()
