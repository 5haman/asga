### Task 08 – Critic Agent

**Goal**  
LLM-judge via OpenRouter.

**Tests**

| Case | Expect |
|------|--------|
| Bad patch | Score < 0.7; blocks merge. |
| Good patch | Score ≥ 0.8; passes. |
| Schema | Output matches `Critique.v1`. |