"""Autogen Agent (OpenRouter) — Minimal JSON enforcement without dspy.guardrails

Removes dependency on `dspy.guardrails`. Instead, a simple manual retry loop
checks that required output fields are not empty and re-prompts the model
(up to 3 attempts) with stronger JSON instructions.
"""

from __future__ import annotations
from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    OPENROUTER_MAX_TOKENS,
)
from typing import TypedDict, Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel
import dspy
from langgraph.graph import StateGraph, START, END

# ─── LM via OpenRouter ───────────────────────────────────────────────────────
OR_API_KEY = OPENROUTER_API_KEY
if not OR_API_KEY:
    raise RuntimeError("Set OPENROUTER_API_KEY before launching the server.")
OR_MODEL = OPENROUTER_MODEL
OR_MAX_TOKENS = OPENROUTER_MAX_TOKENS

lm = dspy.LM(
    f"openai/{OR_MODEL}",
    api_key=OR_API_KEY,
    api_base="https://openrouter.ai/api/v1",
    model_type="chat",
    temperature=0.3,
    max_tokens=OR_MAX_TOKENS,
)
dspy.configure(lm=lm)


# ─── MCP Stub ────────────────────────────────────────────────────────────────
class MCPClient:
    def __init__(self, host: str = "http://localhost:8900"):
        self.host = host

    def publish(self, artifact: Dict[str, Any]) -> None:
        print(f"[MCP] Publishing to {self.host}:\n{artifact}\n")


# ─── DSPy Signatures ─────────────────────────────────────────────────────────
JSON_NOTE = (
    "Respond ONLY with valid JSON for the OutputField(s). "
    "Do NOT add any extra keys or prose."
)


class SpecExtractor(dspy.Signature):
    """Extract structured spec from a user story.
    {JSON_NOTE}
    """

    user_story: str = dspy.InputField(desc="End‑user story")
    spec: str = dspy.OutputField(desc="Markdown bullet list")


class CodeGenerator(dspy.Signature):
    """Generate Python code that fulfils the spec.
    {JSON_NOTE}
    """

    spec: str = dspy.InputField(desc="Requirements")
    code: str = dspy.OutputField(desc="Python source code")


class Evaluator(dspy.Signature):
    """Critique the generated code and suggest improvements.
    {JSON_NOTE}
    """

    code: str = dspy.InputField(desc="Generated code")
    evaluation: str = dspy.OutputField(desc="Feedback on code")


# ─── Utility: simple retry wrapper ───────────────────────────────────────────
def call_with_retries(module: dspy.Predict, attempts: int = 3, **kwargs):
    """Call a dspy.Predict object, retrying until all OutputFields are non‑empty."""
    last = None
    for i in range(attempts):
        last = module(**kwargs)
        # Check any None / empty values
        missing = [k for k, v in last.items() if not v and k not in kwargs]
        if not missing:
            return last
        # Strengthen prompt if missing
        kwargs = {**kwargs, **{k: "" for k in missing}}
    return last  # may still be incomplete


# Instantiate predictors
spec_predict = dspy.Predict(SpecExtractor)
code_predict = dspy.Predict(CodeGenerator)
eval_predict = dspy.Predict(Evaluator)


# ─── Shared State ────────────────────────────────────────────────────────────
class AgentState(TypedDict, total=False):
    user_story: str
    spec: str
    code: str
    evaluation: str


# ─── Node handlers ───────────────────────────────────────────────────────────
def extract_spec(state: AgentState) -> Dict[str, Any]:
    res = call_with_retries(spec_predict, user_story=state["user_story"])
    return {"spec": res.spec}


def generate_code(state: AgentState) -> Dict[str, Any]:
    res = call_with_retries(code_predict, spec=state["spec"])
    return {"code": res.code}


def evaluate(state: AgentState) -> Dict[str, Any]:
    res = call_with_retries(eval_predict, code=state["code"])
    return {"evaluation": res.evaluation}


# ─── Build StateGraph ────────────────────────────────────────────────────────
builder = StateGraph(AgentState)
builder.add_node("extract_spec", extract_spec)
builder.add_node("generate_code", generate_code)
builder.add_node("evaluate", evaluate)
builder.add_edge(START, "extract_spec")
builder.add_edge("extract_spec", "generate_code")
builder.add_edge("generate_code", "evaluate")
builder.add_edge("evaluate", END)

graph = builder.compile()

# ─── FastAPI App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Autogen Agent (OpenRouter minimal)",
    version="0.7.0",
    description="LangGraph + DSPy agent without dspy.guardrails dependency.",
)


class GenerateRequest(BaseModel):
    user_story: str


@app.post("/generate")
def generate(req: GenerateRequest):
    result: AgentState = graph.invoke({"user_story": req.user_story})  # type: ignore[arg-type,assignment]
    MCPClient().publish(result)  # type: ignore[arg-type]
    return result
