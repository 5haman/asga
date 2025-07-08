### Task 03 – LangGraph Workflow

**Goal**  
Implement `src/graph/workflow.py` as a **LangGraph StateGraph** with nodes Spec→Test→Code→Critic→Repair and a Supervisor router.

**Tests**

| Case | Expectation |
|------|-------------|
| Happy-path | Mock agents signal `SUCCESS`; graph returns merged patch. |
| Critic-fail | Critic < 0.7 triggers Repair loop; cap at 3 iterations. |
| Trace | `otel-test-utils` confirms `trace_id` propagates across nodes. |