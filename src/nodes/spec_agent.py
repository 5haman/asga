from __future__ import annotations

import json
from typing import Dict, Any

from config import (
    OPENROUTER_MODEL,
    OPENROUTER_MAX_TOKENS,
    OPENROUTER_API_KEY,
    OPENROUTER_SEED,
)

import dspy
from dspy.teleprompt import SIMBA
from dspy.primitives.example import Example
from langfuse import observe
from generated.contracts.v1 import contracts_pb2 as pb
from utils import get_logger, validate_envelope


# --- OpenRouter client configuration --------------------------------------
MODEL = OPENROUTER_MODEL
MAX_TOKENS = OPENROUTER_MAX_TOKENS
API_KEY = OPENROUTER_API_KEY
SEED = OPENROUTER_SEED

lm = dspy.LM(
    f"openai/{MODEL}",
    api_key=API_KEY,
    api_base="https://openrouter.ai/api/v1",
    model_type="chat",
    temperature=0,
    max_tokens=MAX_TOKENS,
)
dspy.configure(lm=lm)


class SpecExtractor(dspy.Signature):
    """Extract API spec from a feature request."""

    user_story: str = dspy.InputField(desc="End‑user story")
    endpoint: str = dspy.OutputField(desc="Endpoint path")
    method: str = dspy.OutputField(desc="HTTP verb")
    request_schema: str = dspy.OutputField(desc="Request schema JSON")
    response_schema: str = dspy.OutputField(desc="Response schema JSON")


# Small training set for SIMBA
_trainset = [
    Example(
        user_story="upload a file",
        endpoint="/files",
        method="POST",
        request_schema="{}",
        response_schema="{}",
    ).with_inputs("user_story"),
    Example(
        user_story="list files",
        endpoint="/files",
        method="GET",
        request_schema="{}",
        response_schema="{}",
    ).with_inputs("user_story"),
]

_simba = SIMBA(metric=lambda ex, pred: 1.0, bsize=1, max_steps=1)
spec_predictor = _simba.compile(
    dspy.Predict(SpecExtractor), trainset=_trainset, seed=SEED
)


def _call_llm(user_story: str) -> tuple[dict, int]:
    try:
        res = spec_predictor(user_story=user_story)
        usage = getattr(res._raw_output, "usage", None)
        tokens = getattr(usage, "total_tokens", 0) if usage else 0
        return {
            "endpoint": res.endpoint,
            "method": res.method,
            "request_schema": json.loads(res.request_schema or "{}"),
            "response_schema": json.loads(res.response_schema or "{}"),
        }, tokens
    except Exception:
        return {
            "endpoint": "/demo",
            "method": "GET",
            "request_schema": {},
            "response_schema": {},
        }, 0


logger = get_logger(__name__)


def _validate_spec(spec: pb.Spec) -> None:  # type: ignore[name-defined]
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
    validate_envelope(envelope, "spec")


@observe()
def spec_node(state: Dict[str, Any]) -> Dict[str, Any]:
    feature: pb.FeatureRequest = state["feature_request"]  # type: ignore[name-defined]
    text = feature.user_story
    logger.debug("spec_node input: %s", text)
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
    logger.debug("spec_node generated spec: %s", spec)
    if tokens >= MAX_TOKENS:
        raise ValueError("token budget exceeded")
    result = {"spec": spec, "token_count": tokens}
    logger.debug("spec_node output: %s", result)
    return result
