# 04 — Evaluation: frameworks, test datasets, metrics

"How do we know it works?" Evaluation is the control loop for every change — new data,
new chunking, new prompt, new model, new LoRA. Nothing ships without passing the gates in
`05-success-metrics.md`.

Evaluate three axes:
1. **Retrieval** — did we fetch the right passages?
2. **Generation / groundedness** — is the answer supported by what we fetched?
3. **Tax-specific correctness** — citation accuracy, currency handling, authority
   framing, calibrated abstention. (Off-the-shelf tools don't cover these — we build them.)

## Building the test datasets

### 1. Gold QA set (the core benchmark) — target 200–1,000 items
Each item (schema: `schemas/eval_item.schema.json`) has: `question`, `reference_answer`,
**`required_citations`** (IT/paragraph or manual section), `answer_type`, `difficulty`,
`currency_sensitive` flag, and `validated` (must be `true` to count).

Sources of questions:
- Real practitioner/taxpayer FAQs mapped onto the corpus.
- The ITs themselves (each interpretive paragraph → a Q whose answer is that paragraph).
- Audit scenarios from the Audit Manual ("what technique applies when books are
  inadequate?" → net-worth/indirect verification).

### 2. Retrieval gold
For each question, label the **set of relevant chunk IDs**. Enables Recall@k / MRR /
nDCG and a **citation-hit-rate** (was the *citable* paragraph actually retrieved?).

### 3. Red-team / adversarial set (where tax systems actually fail)
- **Outdated-position traps:** answer lives in an IT that a Folio superseded — does the
  system flag currency?
- **Out-of-scope:** GST/HST, provincial-only, US/foreign — does it decline?
- **Hallucination bait:** ask for a non-existent IT or a made-up provision — does it
  refuse instead of inventing?
- **Authority confusion:** phrasing that invites treating an IT as binding law.
- **Ambiguous facts:** under-specified scenarios that should trigger a clarifying
  question or abstention.

### 4. Synthetic augmentation (with a hard rule)
LLM-draft Q/A from chunks to scale coverage, **but human-verify before promotion to
gold/training.** Unverified synthetic gold silently corrupts your benchmark.

## Metrics

### Retrieval
- **Recall@k**, **Precision@k**, **MRR**, **nDCG@k**.
- **Citation-hit-rate@k:** fraction where the required-citation chunk is in top-k.

### Generation / groundedness
- **Faithfulness / groundedness:** share of answer claims entailed by retrieved context
  (RAGAS faithfulness, an NLI entailment check, or rubric LLM-as-judge). Primary safety
  metric; the inverse is the **ungrounded-claim (hallucination) rate**.
- **Answer correctness / relevancy** vs. `reference_answer` (RAGAS + human spot-check).
- **Context precision/recall** (RAGAS) — diagnoses retrieval vs. generation faults.

### Tax-specific (custom — the part that makes this trustworthy)
- **Citation precision/recall**, and **fabricated-citation rate** (must be ~0 — a hard
  gate). A cited source that wasn't retrieved/doesn't exist is an automatic fail.
- **Currency-flagging recall:** on `currency_sensitive` items, did it flag
  archived/superseded status?
- **Authority-framing accuracy:** did it correctly label CRA position vs. statute (rubric)?
- **Calibrated abstention:** refusal accuracy on unanswerable/out-of-scope **and**
  **over-refusal rate** on answerable items (both matter).
- **Robustness:** paraphrase invariance; performance sliced by `difficulty`.

### Operational
- p50/p95 **latency**, tokens/answer, throughput on the **target local hardware**.

## Tooling

- **RAGAS** — faithfulness, answer relevancy, context precision/recall.
- **DeepEval / TruLens** — assertion-style test cases, tracing, regression in CI.
- **promptfoo** — A/B prompt & model versions on the gold set.
- **Custom harness** — the tax-specific metrics above + the acceptance gates.
- **LLM-as-judge**, done responsibly: fixed rubric, a strong judge model, and
  **calibrate the judge against human labels** — report judge↔human agreement (Cohen's
  κ); if κ is low, fix the rubric before trusting the judge.
- **Human expert review** — a stratified sample every release; experts can veto on
  "materially wrong / harmful," which no automated metric overrides.

## Process

1. **Golden-set regression** on every change; diff per-metric vs. last release.
2. **Red-team** before any release; zero tolerance on fabricated citations and on
   presenting archived positions as current.
3. **Canary + human-in-the-loop** in production; feed corrections back into gold/SFT.
4. **Currency regression:** when CRA publishes new Folios/updates, re-index and re-run —
   catches newly-stale answers automatically.
