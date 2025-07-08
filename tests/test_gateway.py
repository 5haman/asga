import json
import pytest
from httpx import AsyncClient, ASGITransport
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from gateway import create_app

@pytest.fixture()
def setup_app():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace._set_tracer_provider(provider, False)  # type: ignore[attr-defined]
    app = create_app()
    return app, exporter


@pytest.mark.asyncio
async def test_gateway_endpoints(setup_app):
    app, exporter = setup_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/jobs", json={"user_story": "hi"})
        assert res.status_code == 200
        job_id = res.json()["job_id"]

        events = []
        async with client.stream("GET", f"/jobs/{job_id}") as sse:
            assert sse.status_code == 200
            async for line in sse.aiter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))
        assert events

        prm = await client.get("/prompt/prompts")
        assert prm.status_code == 200

        openapi = await client.get("/openapi.json")
        assert openapi.status_code == 200
        assert "trace_id" in openapi.headers

    trace.get_tracer_provider().force_flush()  # type: ignore[attr-defined]
    spans = exporter.get_finished_spans()
    assert len(spans) >= 1


@pytest.mark.asyncio
async def test_gateway_404s(setup_app):
    app, _ = setup_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing = await client.get("/jobs/bad-id")
        assert missing.status_code == 404

        miss_prompt = await client.get("/prompt/missing")
        assert miss_prompt.status_code == 404
