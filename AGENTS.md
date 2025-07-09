# Autonomous Coding System – Agent Charter  
*Runtime stack: **LangGraph · OpenRouter · MCP · FastAPI***

---

## 1 Guiding Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| P-01 | **Determinism** – every LLM call sets `temperature:0`, fixed `seed`, explicit model/version | reproducible agent runs |
| P-02 | **Contract-First** – inter-agent messages validate against protobuf schemas wrapped in **MCP envelopes** | prevents schema drift & hallucinations |
| P-03 | **Graph-Native Execution** – the whole workflow is a LangGraph **StateGraph**; no external orchestrator | simplifies dependency graph & recovery |
| P-04 | **Fail-Fast Testing** – tests precede code; agents cannot merge patches until tests pass locally | codifies TDD for LLM coding |
| P-05 | **Observability by Default** – every FastAPI & LangGraph span emits tracing data | end-to-end latency / cost tracing |
| P-06 | **Budget Awareness** – orchestrator enforces per-job token ceiling; agents self-report usage | avoid runaway spend on OpenRouter |

---

## 2 Agent Roster

| Agent | Responsibility | In | Out | Prompt Template | Quality Gate |
|-------|----------------|----|-----|-----------------|--------------|
| **Spec Agent** | Translate `FeatureRequest.v1` ⇒ `Spec.v1` (endpoints, data models, acceptance criteria) | `FeatureRequest.v1` | `Spec.v1` | `/prompts/spec_v2.md` | Guardrails JSON pass |
| **Test Agent** | Emit failing unit & Hypothesis tests from accepted spec | `Spec.v1` | `Tests.v1` | `/prompts/tests_v2.md` | Tests compile & fail |
| **Code Agent** | Produce minimal patch set that makes tests green | `Spec.v1`,`Tests.v1` | `Patch.v1` | `/prompts/code_v2.md` | `pytest` all-green |
| **Critic Agent** | LLM-judge reviewing patch diff (style, security, complexity) | `Patch.v1` | `Critique.v1` | `/prompts/critic_v2.md` | OpenAI-Evals ≥ 0.8 |
| **Repair Agent** | Analyse critique and plan corrective loop | `Critique.v1` | `RepairPlan.v1` | `/prompts/repair_v2.md` | JSON plan valid |

_All five are implemented as **LangGraph nodes**; the graph’s **Supervisor** hands off control based on state and MCP tool calls._

---

## 3 Communication Protocol

1. **Envelope:** Every payload is binary protobuf **inside** an MCP JSON wrapper (`context`,`request`,`response`,`tool_calls`).  
2. **Transport:** gRPC for intra-process; HTTP/2 for inter-service; FastAPI gateway translates REST ⇆ gRPC.  
3. **Headers:** `trace_id`,`span_id`,`token_count`,`model_id`.  
4. **LLM Gateway:** Agents call `https://openrouter.ai/v1/chat/completions` with **OpenRouter** SDK, allowing model switching & cost optimisation.

---

## 4 Prompt & Tooling Conventions

* **LangGraph StateGraph:** agents are nodes; Supervisor uses `Command` router.  
* **MCP Tool Calling:** agents expose shell, git, pytest as MCP tools; Supervisor decides invocation.  
* **Seed Freezing:** orchestrator injects `hypothesis.settings(seed=…)` for replayable failures.  
* **OpenRouter Models:** default `openrouter/mistral-large-latest`; override per-agent via config.

---

## 5 Evaluation & Safety

* **Evals:** OpenAI-Evals gate each PR – correctness, latency, cost.  
* **Guardrails RAIL:** schema & content filters on every agent output.  
* **Bandit / Semgrep:** block insecure code paths.  
* **Human Escalation:** Repair loop capped at 3; critic score < 0.7 triggers manual review.

---

## 6 Observability Stack

| Layer | Instrumentation | Exporter |
|-------|-----------------|----------|
| FastAPI | built-in logging hooks | OTLP → Tempo |
| LangGraph | custom `@graph.span` decorator | OTLP → Tempo |
| Grafana | dashboards: `latency`, `token_spend`, `pass_rate` | Tempo + Loki |

---

## 7 Glossary

* **MCP** – Model Context Protocol, standardising context/tool packets.  
* **StateGraph** – typed DAG in LangGraph managing stateful agent execution.  * **Supervisor** – routing LLM node that decides next agent.
## 8 Main Cycle

```mermaid
graph TD
  subgraph Main cycle
    A[clone/pull] --> B[analyse]
    B --> C[collect product signals]
    C --> D[plan changes]
    D -->|refactor| E[generate patch]
    D -->|feature|  F[generate feature code]
    E --> G[apply & test]
    F --> G
    G --> H[LLM+MCP review]
    H -->|accept| I[create PR]
    H -->|reject| J[optimise SIMBA]
  end
```

**LangGraph nodes & actions**
- **clone / pull** – helper `git_clone_or_pull()` using GitPython.
- **analyse** – run `pylint` and `lizard`, capture complexity snapshot.
- **collect_signals** – gather churn, heat-map and open issues via codemetrics & GitHub GraphQL.
- **plan_changes** – LLM emits markdown plan with `refactor:` / `feature:` tags.
- **gen_patch** – diff-based patch generation.
- **gen_feature** – iterative spec→tests→impl cycle.
- **apply_test** – apply patches then run `pytest` in a venv.
- **review** – LLM critique published to MCP.
- **create_pr** – open GitHub PR via REST v3.
- **optimise_simba** – internal optimisation loop when review rejects.

