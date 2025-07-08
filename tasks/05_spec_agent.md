### Task 05 – Spec Agent (OpenRouter)

**Goal**  
Implement `nodes/spec_agent.py` calling OpenRouter SDK.

**Tests**

| Scenario | Expectation |
|----------|-------------|
| Nominal | Sample feature → valid `Spec.v1` (Guardrails pass). |
| Injection | Adversarial prompt blocked with structured error. |
| Budget | `token_count` < configured limit. |