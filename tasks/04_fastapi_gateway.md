### Task 04 – FastAPI Gateway

**Goal**  
Expose endpoints:  
* `POST /jobs` → start graph run  
* `GET  /jobs/{id}` → stream events (SSE)  
* `GET  /prompt/{name}` → serve versioned templates

**Tests**

| Type | Check |
|------|-------|
| API | `pytest-asyncio` verifies 200 responses & OpenAPI docs. |
| OTel | Auto-instrumentation adds `trace_id` header; validated via mock collector. |