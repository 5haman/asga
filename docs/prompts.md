# Prompt Pack – Autonomous Software Generation Agent

> Drop‑in, copy‑pastable prompts covering the entire lifecycle: **ideation → spec → code → tests → eval → self‑repair → release**.

---

## 0 · Global System Message

```text
You are the code‑generation agent for {{product_name}}.
Follow **all acceptance criteria** and stay within **existing architecture** shown in the repo tree.
Think step‑by‑step, cite assumptions inline, and end every answer with “<END>”.
```

---

## 1 · Feature Ideation

```text
### USER STORY
{{brief_one-sentence_goal}}

### TASK
1. List five concrete features that satisfy the story.  
2. For each feature give:  
   • one happy‑path scenario  
   • one accessibility or abuse edge‑case  

Format exactly as valid YAML under a top-level key `features`.
```

---

## 2 · Spec & Contract Draft

```text
### CONTEXT
— Repository root: {{tree_snippet}}  
— Coding conventions: {{link_or_doc}}

### TASK
Emit a JSON object with keys:
- `endpoint`: kebab case
- `method`: GET | POST | …
- `request_schema`: JSON‑Schema draft‑2020‑12
- `response_schema`: JSON‑Schema draft‑2020‑12
- `acceptance_criteria`: list of Gherkin‑style bullets

Return ONLY the JSON.
```

---

## 3 · Self‑Review Prompt

```text
Below is a spec you just wrote.

{{spec_json}}

Critique this spec: list ambiguities, missing edge‑cases, or policy violations.  
Then output a corrected spec in the same JSON layout.
```

---

## 4 · Code Scaffold

```text
### GOAL
Generate minimal but runnable code for the approved spec.

### CONSTRAINTS
- Touch only files under `/generated/`.
- Use {{framework}} idioms (see examples below).
- Include TODO comments where business logic is stubbed.
```

---

## 5 · Unit‑Test Generation

```text
For every public function in `/generated/`:
1. Write ≥ 1 happy‑path pytest.  
2. Write ≥ 2 boundary tests focusing on edge‑cases found earlier.

Each test must:
- use existing fixtures in `conftest.py`
- assert explicit values (no bare `assert result`)
- start with docstring "EXPECTED: …"
```

---

## 6 · Property‑Based Tests

```text
Augment the unit tests with Hypothesis.

For every pure function, define a property that must hold for
ALL inputs (e.g., idempotence, monotonicity, commutativity).

Return a single file `test_properties.py`.
```

---

## 7 · Security / External‑Call Check

```text
Scan the diff. Output a table (markdown) with each new outbound
URL or library call and its purpose.  
Flag any entry not in the allow‑list below:
{{comma_separated_allowlist}}
```

---

## 8 · RAG‑Triad Evaluation (Retrieval Apps)

```text
Given this <question, retrieved_context, answer> triple, assign:
- context_relevance: 0‑5
- groundedness: 0‑5
- answer_relevance: 0‑5
Explain each score in one sentence.

Return JSON: {scores:{…}, explanation:{…}}
```

---

## 9 · LLM‑as‑Judge Eval (Generic)

```text
TASK
Compare `candidate_answer` to `reference_answer`.

Return:
{
  "exact_match": true|false,
  "grading_rubric": "{{link}}",
  "score_0_to_1": float,
  "justification": one short paragraph
}
```

---

## 10 · Self‑Repair Loop

```text
### CONTEXT
Tests or evals failed with the log below.

{{ci_log_excerpt}}

### TASK
1. Diagnose root cause in ≤ 200 words.  
2. Propose a patch diff limited to `/generated/`.  
3. Explain why the fix works.
```

---

## 11 · Bias / Safety Audit

```text
Evaluate the model on the Phare benchmark safety suite.
Return a markdown summary table of any metric below threshold.
```

---

## 12 · Regression Schedule (CI Example)

```yaml
name: nightly-evals
on:
  schedule:
    - cron: "0 1 * * *"   # 01:00 UTC daily
jobs:
  run-evals:
    uses: openai/evals-action@v1
    with:
      suite: reg_suite.yaml
```
