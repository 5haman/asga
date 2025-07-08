### Task 13 – Main Cycle

**Goal**
Integrate the full LangGraph cycle from repository clone to PR creation, including SIMBA optimisation on critique failure.

**Tests**

| Case | Expectation |
|------|-------------|
| Clone | Repository is cloned or updated via GitPython. |
| Plan | `plan_changes` output contains `refactor:` and `feature:` tags. |
| Review reject | Negative critique triggers `optimise_simba`. |
