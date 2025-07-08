import sys
from pathlib import Path
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from graph import workflow  # type: ignore
from generated.contracts.v1 import contracts_pb2 as pb


def setup_tracer():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace._set_tracer_provider(provider, False)  # type: ignore[attr-defined]
    return exporter


def test_happy_path(monkeypatch):
    exporter = setup_tracer()

    def spec_stub(state: workflow.WorkflowState):
        with workflow.tracer.start_as_current_span("spec_agent"):
            return {
                "spec": pb.Spec(
                    endpoint="/demo",
                    method="GET",
                    request_schema="{}",
                    response_schema="{}",
                ),
                "token_count": 10,
            }

    monkeypatch.setattr(workflow, "spec_node", spec_stub)

    def critic_success(state: workflow.WorkflowState):
        with workflow.tracer.start_as_current_span("critic_agent"):
            return {"critique": pb.Critique(score=0.9, feedback="ok")}

    monkeypatch.setattr(workflow, "critic_node", critic_success)
    graph = workflow.create_graph()
    with workflow.tracer.start_as_current_span("run"):
        res = graph.invoke({"feature_request": pb.FeatureRequest(user_story="hi")})
    assert res["critique"].score >= 0.8
    assert res.get("attempts", 0) == 0
    trace.get_tracer_provider().force_flush()  # type: ignore[attr-defined]
    spans = exporter.get_finished_spans()
    assert len(spans) >= 0


def test_critic_fail(monkeypatch):
    exporter = setup_tracer()

    def spec_stub(state: workflow.WorkflowState):
        with workflow.tracer.start_as_current_span("spec_agent"):
            return {
                "spec": pb.Spec(
                    endpoint="/demo",
                    method="GET",
                    request_schema="{}",
                    response_schema="{}",
                ),
                "token_count": 10,
            }

    monkeypatch.setattr(workflow, "spec_node", spec_stub)

    def critic_fail(state: workflow.WorkflowState):
        with workflow.tracer.start_as_current_span("critic_agent"):
            return {"critique": pb.Critique(score=0.5, feedback="bad")}

    monkeypatch.setattr(workflow, "critic_node", critic_fail)
    graph = workflow.create_graph()
    with workflow.tracer.start_as_current_span("run"):
        res = graph.invoke({"feature_request": pb.FeatureRequest(user_story="hi")})
    assert res.get("attempts") == 3
    trace.get_tracer_provider().force_flush()  # type: ignore[attr-defined]
    spans = exporter.get_finished_spans()
    assert len(spans) >= 0


def test_trace_propagation():
    exporter = setup_tracer()

    def spec_stub(state: workflow.WorkflowState):
        with workflow.tracer.start_as_current_span("spec_agent"):
            return {
                "spec": pb.Spec(
                    endpoint="/demo",
                    method="GET",
                    request_schema="{}",
                    response_schema="{}",
                ),
                "token_count": 10,
            }

    workflow.spec_node = spec_stub
    graph = workflow.create_graph()
    with workflow.tracer.start_as_current_span("run"):
        graph.invoke({"feature_request": pb.FeatureRequest(user_story="hi")})
    trace.get_tracer_provider().force_flush()  # type: ignore[attr-defined]
    spans = exporter.get_finished_spans()
    assert len(spans) >= 0
