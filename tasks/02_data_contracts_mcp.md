### Task 02 – Data Contracts + MCP

**Goal**  
Define `.proto` messages (`FeatureRequest`, `Spec`, `Tests`, `Patch`, `Critique`, `RepairPlan`) **and** wrap them in MCP JSON-Schema definitions (`schemas/mcp/*.json`).

**Tests**

| Type | Check |
|------|-------|
| Proto | `buf lint` passes; regenerated stubs diff-clean. |
| MCP | `pytest tests/test_mcp_schema.py` validates each JSON sample against MCP schema. |