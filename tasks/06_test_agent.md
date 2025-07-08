### Task 06 – Test Agent

**Goal**  
Generate deterministic failing tests.

**Tests**

| Type | Check |
|------|-------|
| Compilation | `pytest --collect-only` passes. |
| Determinism | Two generations with same seed identical hash. |
| Failure | Initial `pytest` exit code ≠ 0. |