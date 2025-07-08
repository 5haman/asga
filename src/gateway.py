from __future__ import annotations

import asyncio
import json
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, PlainTextResponse
from google.protobuf.json_format import MessageToDict
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel

from generated.contracts.v1 import contracts_pb2 as pb
from graph import workflow


class FeatureRequestModel(BaseModel):
    user_story: str


def create_app() -> FastAPI:
    app = FastAPI(title="ASGA Gateway", version="0.1.0")
    FastAPIInstrumentor().instrument_app(app)

    jobs: dict[str, asyncio.Queue] = {}
    app.state.jobs = jobs

    @app.middleware("http")
    async def add_trace_id_header(request: Request, call_next):
        response = await call_next(request)
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx.trace_id:  # pragma: no branch - header added only when tracing
            trace_id = format(ctx.trace_id, "032x")
            response.headers["trace_id"] = trace_id
        return response

    @app.post("/jobs")
    async def start_job(req: FeatureRequestModel):
        job_id = str(uuid4())
        queue: asyncio.Queue = asyncio.Queue()
        jobs[job_id] = queue
        loop = asyncio.get_running_loop()

        def _serialise(val):
            if hasattr(val, "ListFields"):
                return MessageToDict(val)
            if isinstance(val, dict):
                return {k: _serialise(v) for k, v in val.items()}
            return val  # pragma: no cover - simple passthrough

        def run():  # pragma: no cover - executed in thread
            for event in workflow.graph.stream(
                {"feature_request": pb.FeatureRequest(user_story=req.user_story)}
            ):
                serialised = {k: _serialise(v) for k, v in event.items()}
                asyncio.run_coroutine_threadsafe(queue.put(serialised), loop)
            asyncio.run_coroutine_threadsafe(queue.put(None), loop)

        loop.run_in_executor(None, run)  # pragma: no cover - scheduling thread
        return {"job_id": job_id}

    @app.get("/jobs/{job_id}")
    async def job_events(job_id: str):
        if job_id not in jobs:
            raise HTTPException(404, "job not found")
        queue = jobs[job_id]

        async def event_generator():
            try:
                while True:
                    event = await queue.get()
                    if event is None:
                        break
                    yield f"data: {json.dumps(event)}\n\n"
            finally:
                jobs.pop(job_id, None)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.get("/prompt/{name}")
    async def get_prompt(name: str):
        path = Path("docs") / f"{name}.md"
        if not path.exists():
            raise HTTPException(404, "Prompt not found")
        return PlainTextResponse(path.read_text())

    return app


app = create_app()
