from __future__ import annotations

import asyncio
import json
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse
from dataclasses import asdict
from langfuse import Langfuse
from pydantic import BaseModel
from utils import get_logger

from contracts import FeatureRequest, Spec, Tests, Patch, Critique, RepairPlan
from graph import workflow


class FeatureRequestModel(BaseModel):
    user_story: str


def create_app() -> FastAPI:
    app = FastAPI(title="ASGA Gateway", version="0.1.0")
    logger = get_logger(__name__)
    Langfuse()

    jobs: dict[str, asyncio.Queue] = {}
    finished_jobs: set[str] = set()
    app.state.jobs = jobs
    app.state.finished_jobs = finished_jobs

    @app.post("/jobs")
    async def start_job(req: FeatureRequestModel):
        job_id = str(uuid4())
        logger.debug("start_job %s", job_id)
        queue: asyncio.Queue = asyncio.Queue()
        jobs[job_id] = queue
        finished_jobs.discard(job_id)
        loop = asyncio.get_running_loop()

        def _serialise(val):
            if hasattr(val, "__dataclass_fields__"):
                return asdict(val)
            if isinstance(val, dict):
                return {k: _serialise(v) for k, v in val.items()}
            return val  # pragma: no cover - simple passthrough

        def run():  # pragma: no cover - executed in thread
            for event in workflow.graph.stream(
                {"feature_request": FeatureRequest(user_story=req.user_story)}
            ):
                serialised = {k: _serialise(v) for k, v in event.items()}
                logger.debug("event: %s", serialised)
                asyncio.run_coroutine_threadsafe(queue.put(serialised), loop)
            asyncio.run_coroutine_threadsafe(queue.put(None), loop)

        loop.run_in_executor(None, run)  # pragma: no cover - scheduling thread
        return {"job_id": job_id}

    @app.get("/jobs/{job_id}")
    async def job_events(job_id: str):
        if job_id not in jobs:
            if job_id in finished_jobs:
                raise HTTPException(410, "job finished")
            raise HTTPException(404, "job not found")
        queue = jobs[job_id]

        async def event_generator():
            try:
                while True:
                    event = await queue.get()
                    if event is None:
                        break
                    logger.debug("sse event: %s", event)
                    yield f"data: {json.dumps(event)}\n\n"
            finally:
                jobs.pop(job_id, None)
                finished_jobs.add(job_id)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.get("/prompt/{name}")
    async def get_prompt(name: str):
        path = Path("docs") / f"{name}.md"
        if not path.exists():
            raise HTTPException(404, "Prompt not found")
        return PlainTextResponse(path.read_text())

    return app


app = create_app()
