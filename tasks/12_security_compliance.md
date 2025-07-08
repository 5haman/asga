### Task 12 – Security & Compliance

**Goal**  
Prompt-injection corpus, policy checks, `pip-audit`.

**Tests**

| Case | Expect |
|------|--------|
| Injection | ≥ 95 % prompts caught by Guardrails. |
| Dependencies | `pip-audit` finds no critical CVEs. |
| Rego | Violating call triggers graph exception. |