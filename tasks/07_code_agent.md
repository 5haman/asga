### Task 07 – Code Agent

**Goal**  
Produce patch turning tests green.

**Tests**

| Type | Check |
|------|-------|
| Green | `pytest` passes after patch. |
| Complexity | `radon cc` ≤ threshold. |
| Snapshot | `.diff` file hash stable. |