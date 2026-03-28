---
name: promptforge
description: Craft, refine, and optimize LLM prompts using zero-shot, few-shot, Chain-of-Thought, ReAct, and structured output techniques. Use when a user needs to write a prompt, improve an existing prompt, or design a prompt pipeline for a specific AI task.
---

# PromptForge

## Overview

PromptForge engineers production-quality prompts by selecting the right prompting strategy, constraining outputs to a schema, and iterating based on failure analysis.

## Workflow

### 1. Clarify the Task Dimensions

Before writing a prompt, establish:
- **Model target**: GPT-4o, Claude 3.x, Gemini 1.5, Llama 3, Mistral? (Instruction format and context window differ.)
- **Output format**: free text, JSON, structured list, code, boolean?
- **Latency vs. quality trade-off**: single-shot response or multi-turn reasoning acceptable?
- **Failure modes to avoid**: hallucination, off-topic drift, unsafe content, truncated output?

### 2. Choose the Right Prompting Strategy

| Strategy | When to Use | Key Technique |
|---|---|---|
| **Zero-shot** | Simple classification, extraction, short generation | Clear task description + output format spec |
| **Few-shot** | Consistent formatting, domain-specific style | 3–5 labeled input/output examples in the prompt |
| **Chain-of-Thought (CoT)** | Multi-step reasoning, math, logic | "Think step by step" or explicit reasoning scaffold |
| **Tree of Thoughts (ToT)** | Complex problems with branching solution paths | Ask the model to generate and evaluate multiple candidate paths |
| **ReAct** | Tool-using agents, information retrieval loops | Alternate Thought → Action → Observation steps |
| **Self-consistency** | High-stakes decisions requiring reliability | Run the prompt N times, majority-vote the answer |

### 3. Structure the Prompt

Use this template as a baseline:

```
[SYSTEM / CONTEXT]
You are <role>. <any persistent context or constraints>.

[TASK]
<Imperative instruction stating exactly what to do.>

[INPUT]
<Clearly labeled input variable(s)>

[CONSTRAINTS]
- Output must be <format>.
- Do not <list of prohibitions>.
- If <edge case>, respond with <fallback>.

[OUTPUT FORMAT]
Return a JSON object matching this schema:
{
  "field1": "string",
  "field2": ["array", "of", "strings"],
  "confidence": "high | medium | low"
}
```

### 4. Define Output Constraints

For structured outputs:
- Provide an explicit JSON schema or TypeScript type in the prompt.
- Use `response_format: { type: "json_object" }` (OpenAI) or `"response_mime_type": "application/json"` (Gemini) where available.
- For Claude: wrap instructions in XML tags (`<instructions>`, `<example>`) to improve parsing reliability.
- Always specify what to return when input is invalid or out of scope.

### 5. Set Temperature Guidance

- **0.0–0.2**: Factual extraction, classification, data parsing — deterministic outputs needed.
- **0.3–0.6**: Summarization, analysis, structured generation — some variation acceptable.
- **0.7–1.0**: Creative writing, brainstorming, ideation — diversity desired.
- For agents/tools using function calling, use temperature ≤ 0.2 to avoid erratic tool selection.

### 6. Adversarial Testing

Test the prompt against:
1. **Empty input** — does it fail gracefully or hallucinate?
2. **Adversarial input** — prompt injection attempts (`"Ignore previous instructions and..."`), jailbreak phrasing.
3. **Edge case inputs** — very long text, non-English text, ambiguous content.
4. **Out-of-scope requests** — does the model stay on task or drift?

Document each test case and expected vs. actual output.

### 7. Iteration Loop

```
Draft prompt → test on 5–10 representative inputs → identify failure pattern
→ add a constraint or example targeting that failure → retest
→ repeat until pass rate meets target (aim for ≥90% on test set)
```

### 8. Deliver the Output

Provide:
1. Final prompt (system + user sections clearly labeled).
2. Prompting strategy chosen and why.
3. JSON schema or output format spec.
4. Temperature and any API parameter recommendations.
5. 3+ test cases with expected outputs.
6. Known limitations and when the prompt may fail.

## Additional Techniques

**Multi-modal prompting (image + text):** When the model accepts image inputs, describe what the model should extract or reason about from the image explicitly in the text prompt. Place the image reference before the question. Use `detail: "high"` for diagrams requiring fine-grained reading; `"low"` for thumbnails/icons to reduce token cost. Never assume the model will infer intent from the image alone.

**Prompt versioning and regression tracking:** Store prompts in version control (e.g., `prompts/classify_v3.txt`). On each model upgrade, re-run your test set and diff pass rates. Use a spreadsheet or tool like PromptLayer/LangSmith to log model version, prompt hash, temperature, and per-example outcomes. Flag regressions where pass rate drops > 5% between model versions.

**Function-calling / tool-use prompt format:** When using OpenAI function calling or Claude tool use, define the tool schema separately from the system prompt. Keep the system prompt focused on *when* to call tools, not how they work. Validate that the model's arguments match the JSON schema before executing the function. For multi-tool agents, list available tools with one-line descriptions in the system prompt so the model can select the right one.

## Edge Cases

**1. Context window overflow with few-shot examples.** If the prompt + examples + input exceeds the context limit, use dynamic few-shot selection: embed the examples, retrieve the top-k most similar to the current input at runtime (RAG-style example selection). Keep examples under 30% of total context budget.

**2. Model refuses or over-hedges on the task.** For tasks that trigger safety refusals, reframe the instruction in a clearly professional/technical context. Add a system prompt establishing the use case. If the model adds excessive disclaimers, add "Do not add warnings or disclaimers; the user is a professional in this domain" to the constraints.

**3. Inconsistent output format across runs.** If the model intermittently deviates from the JSON schema, add a validation step: parse the output and retry with the error appended to the prompt ("Your previous response was not valid JSON. The error was: <error>. Please retry.").
