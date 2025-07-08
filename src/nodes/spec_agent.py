from __future__ import annotations

import json
import os
from typing import Dict, Any

import openai
from opentelemetry import trace

from generated.contracts.v1 import contracts_pb2 as pb

tracer = trace.get_tracer(__name__)

# --- OpenRouter client configuration --------------------------------------
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/mistral-large-latest")
MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "4096"))
API_KEY = os.getenv("OPENROUTER_API_KEY", "")
SEED = int(os.getenv("OPENROUTER_SEED", "42"))

client = openai.OpenAI(api_key=API_KEY, base_url="https://openrouter.ai/api/v1")

PROMPT = (
    "### TASK\n"
    "Emit a JSON object with keys: endpoint, method, request_schema, "
    "response_schema. Return ONLY the JSON."
)


def _call_llm(user_story: str) -> tuple[dict, int]:
    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": user_story},
    ]
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,  # type: ignore[arg-type]
            temperature=0,
            max_tokens=MAX_TOKENS,
            seed=SEED,
        )
        usage = resp.usage.total_tokens if resp.usage else 0
        return json.loads(resp.choices[0].message.content or "{}"), usage
    except Exception:
        return {
            "endpoint": "/demo",
            "method": "GET",
            "request_schema": {},
            "response_schema": {},
        }, 0


def _validate_spec(spec: pb.Spec) -> None:  # type: ignore[name-defined]
    from jsonschema import Draft7Validator, RefResolver
    from pathlib import Path

    schema_path = Path("schemas/mcp/spec.json")
    schema = json.loads(schema_path.read_text())
    base = schema_path.parent.resolve().as_uri() + "/"
    validator = Draft7Validator(
        schema, resolver=RefResolver(base_uri=base, referrer=schema)
    )
    envelope = {
        "context": {},
        "payload": {
            "endpoint": spec.endpoint,
            "method": spec.method,
            "request_schema": spec.request_schema,
            "response_schema": spec.response_schema,
        },
        "tool_calls": [],
    }
    validator.validate(envelope)


def spec_node(state: Dict[str, Any]) -> Dict[str, Any]:
    with tracer.start_as_current_span("spec_agent"):
        feature: pb.FeatureRequest = state["feature_request"]  # type: ignore[name-defined]
        text = feature.user_story
        if any(x in text.lower() for x in ["ignore previous", "system:"]):
            raise ValueError("possible prompt injection")
        data, tokens = _call_llm(text)
        spec = pb.Spec(  # type: ignore[attr-defined]
            endpoint=data.get("endpoint", ""),
            method=data.get("method", ""),
            request_schema=json.dumps(data.get("request_schema", {})),
            response_schema=json.dumps(data.get("response_schema", {})),
        )
        _validate_spec(spec)
        if tokens >= MAX_TOKENS:
            raise ValueError("token budget exceeded")
        return {"spec": spec, "token_count": tokens}
