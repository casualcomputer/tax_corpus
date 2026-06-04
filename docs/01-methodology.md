# 01 — Methodology: how to "teach" a local LLM tax knowledge

There are three distinct levers. They are **complementary, not alternatives**, and they
solve different problems. The single most common (and expensive) mistake is trying to
fine-tune facts into a model when you should be retrieving them.

## 1. Retrieval-Augmented Generation (RAG) — the backbone

Keep the knowledge **outside** the model in a searchable index; at query time, retrieve
the relevant passages and have the model answer **only** from them, **with citations**.

Why RAG is mandatory (not optional) for tax:

- **Citations & verifiability.** A tax answer is worthless if it can't be traced to a
  source paragraph. RAG gives you the source; a memorized fact cannot be cited.
- **Currency.** Tax changes every year; ITs get superseded by Folios. Re-index → updated
  answers. No retraining. A model that *memorized* a 1995 IT will confidently state stale
  positions forever.
- **Provenance & auditability.** Regulated use demands "where did this come from?" RAG
  records the exact chunk, doc, paragraph, date, and status.
- **Hallucination control.** Constrained-to-context generation + citation verification is
  the most effective lever against fabricated tax positions.

RAG is where ~80% of the quality comes from. Invest here first.

## 2. Supervised fine-tuning (SFT / instruction tuning, via QLoRA/LoRA)

Adjust the weights to change **behavior**, not knowledge:

- Adopt the **register** a tax answer needs: qualified, conditional ("generally",
  "where the following conditions are met"), never over-asserting.
- Enforce **output format**: claim → citation (IT/paragraph or manual section) →
  effective-date/status note → caveat.
- Learn the **task shapes**: "given these facts, identify the relevant provision and
  CRA's administrative position", "summarize an IT", "explain an audit technique".
- Learn **domain vocabulary** and the cross-reference style ("subsection 20(1)(c)",
  "paragraph 8(1)(h.1)").
- Calibrate **abstention/refusal** — when context is insufficient or the question is
  out-of-scope, say so.

How to build SFT data **without** importing stale facts:
- Generate instruction/response pairs **grounded in retrieved chunks** (the response
  cites the chunk it was built from). This teaches the *behavior of grounding*, not the
  fact itself.
- Mine the ITs (already interpretive) into Q→A pairs; **human-verify** a sample.
- Include **negative/abstention** examples and **currency-flagging** examples.

What SFT must **not** do: be used as the primary store of tax facts. Facts baked into
weights go stale, can't be cited, and bleed across cases. Keep facts in the index.

## 3. Continued / domain-adaptive pre-training (DAPT/CPT)

Further pre-train the base model on a large unlabeled tax corpus to build deep domain
fluency. **Usually skip this.** It is expensive (lots of tokens, GPU time), risks
catastrophic forgetting, and — critically — still doesn't give you citable, current
facts. Consider it only when:

- You have a *large* corpus (millions+ of tokens) and
- A strong RAG+SFT baseline still struggles with domain *language/reasoning*, and
- You can afford the compute and a fresh eval each iteration.

## Putting it together (recommended sequence)

1. **Build RAG** over the two sources (see `03-data-engineering.md`). Measure.
2. **Add behavioral QLoRA** once retrieval is solid. Re-measure (watch for regressions).
3. **Only then** consider DAPT, and only if the eval says you need it.

At each step, the **evaluation harness (`04-evaluation.md`) is the control loop.** No
change ships without passing the gates in `05-success-metrics.md`.

## Local-model considerations

You specified **local** LLMs — the right call for tax data privacy/control. Tradeoffs:

- A **7–8B** model (Llama-3.x-8B, Qwen2.5-7B, Mistral) is viable **only** with strong
  hybrid retrieval + a cross-encoder reranker carrying the load; expect it to need tight
  citation guardrails.
- A **32–72B** quantized model (AWQ/GPTQ/GGUF) via vLLM/llama.cpp gives noticeably better
  reasoning and abstention if your hardware allows.
- Use a strong **local embedding** model (bge-large / gte / e5 / nomic-embed) and a
  **local reranker** (bge-reranker) so the entire stack stays on-prem.
- Quantize the generator to fit VRAM; keep the embedding + reranker in full/half precision
  (they're small and quality-sensitive).
