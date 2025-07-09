import json
import pytest
from httpx import AsyncClient, ASGITransport
from gateway import create_app


@pytest.fixture()
def setup_app():
    app = create_app()
    return app


@pytest.mark.asyncio
async def test_gateway_endpoints(setup_app):
    app = setup_app
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


@pytest.mark.asyncio
async def test_job_cleanup(setup_app):
    app = setup_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/jobs", json={"user_story": "cleanup"})
        job_id = res.json()["job_id"]
        assert job_id in app.state.jobs

        async with client.stream("GET", f"/jobs/{job_id}") as sse:
            async for _ in sse.aiter_lines():
                pass

        assert job_id not in app.state.jobs


@pytest.mark.asyncio
async def test_gateway_404s(setup_app):
    app = setup_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing = await client.get("/jobs/bad-id")
        assert missing.status_code == 404

        miss_prompt = await client.get("/prompt/missing")
        assert miss_prompt.status_code == 404
