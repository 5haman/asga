### Task 01 – Repository Skeleton & CI

**Goal**  
Scaffold repo per §11 layout; create GitHub Actions pipeline.

**Tests**

| Type | What it Checks |
|------|----------------|
| Unit | `tests/test_structure.py` asserts required dirs/files exist. |
| Workflow | `act -j ci` validates `.github/workflows/ci.yml`. |
| Smoke | Dummy test `tests/test_placeholder.py` passes. |