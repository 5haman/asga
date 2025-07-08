### Task 10 – CI/CD Enhancements

**Goal**  
Add OpenAI-Evals, SBOM, Bandit, Semgrep.

**Tests**

| Case | Expect |
|------|--------|
| Evals | `openai tools evaluations run` passes threshold. |
| Security | Inject Bandit finding → CI fails. |
| SBOM | `sbom.spdx.json` artifact uploaded. |