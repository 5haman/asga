### Task 11 – Observability

**Goal**  
Deploy Tempo + Grafana; instrument FastAPI & LangGraph.

**Tests**

| Check | Tool |
|-------|------|
| Tempo up | `curl :16686` 200. |
| Span linking | Custom test asserts parent/child ids. |
| Dashboard | Grafana API returns dashboard UID. |