# 07 — Use cases, model choices, training data, and loss functions

The two sources skew toward **compliance, audit, and statutory interpretation**, so the
highest-value products live in **tax administration & processing**. This doc answers:
*which model type for which job, what to train it on (built from the corpus), and how to
define the loss.*

Guiding principle: **use the smallest model that solves the task.** A fine-tuned 400M
embedding model + a classifier head will out-route, out-cost, and out-latency a 70B
generator on document triage. Reserve the generative LLM (+RAG) for open-ended language.
Train retrievers/rerankers/classifiers **separately** — clean losses, cheap, measurable.

---

## A. Use-case portfolio (tax admin / processing)

Maturity: 🟢 crawl · 🟡 walk · 🔴 run.

| # | Use case | Who | Primary model | 🟢🟡🔴 |
|---|---|---|---|---|
| 1 | **Interpretive Q&A / research assistant** ("CRA's position on deductibility of X?") | Auditors, practitioners | RAG + generator | 🟢 |
| 2 | **Semantic search** over corpus | Everyone | Fine-tuned **embeddings** | 🟢 |
| 3 | **Document classification & routing** (T1/T2/objection/election/correspondence) | Intake/processing | **Encoder classifier** | 🟢 |
| 4 | **Issue spotting / provision tagging** (free text → relevant ITA sections / ITs) | Auditors, reviewers | Embeddings (retrieve) + **multi-label classifier** | 🟡 |
| 5 | **Audit-risk triage / case selection** (return → risk score + applicable techniques) | Audit planning | Classifier + RAG (manual) | 🟡 |
| 6 | **Audit-technique recommender** (inadequate books → net-worth/deposit/ratio method) | Auditors | RAG over Audit Manual | 🟡 |
| 7 | **Authority/citation linking & currency check** (draft position → supporting + is-it-current?) | Reviewers | Embeddings + reranker + rules | 🟡 |
| 8 | **Consistency / contradiction checker** (draft vs CRA's stated position) | QA/review | **Cross-encoder NLI** | 🔴 |
| 9 | **Summarization** (IT/Folio/manual chapter, or taxpayer submission) | Everyone | Generator (SFT) | 🟡 |
| 10 | **Drafting assistant** (audit query letters, proposal/position summaries) | Auditors | Generator (SFT + RAG) | 🔴 |
| 11 | **Information extraction** (amounts, dates, provision refs, taxpayer attributes) | Processing | **Token-classifier / structured LLM** | 🟡 |
| 12 | **Objection/appeal triage** (classify grounds, retrieve authorities, est. strength) | Appeals | Classifier + RAG | 🔴 |

A practical **flagship** to build first: **#1 + #2 + #6** (a cited research/recommender
assistant) — it directly exercises the whole RAG stack and de-risks everything else.

---

## B. Model inventory — what each is for

- **Embeddings (bi-encoder)** — retrieval, semantic search, clustering/dedup, candidate
  generation for tagging. *Fine-tune on domain pairs.* (use cases 2,4,5,7,8-candidate)
- **Reranker (cross-encoder)** — precision retrieval, citation relevance, NLI/contradiction.
  (7,8)
- **Encoder classifier (BERT-style + head)** — doc routing, multi-label provision tagging,
  objection-ground classification, risk scoring. (3,4,5,12)
- **Token classifier / structured extractor** — NER for amounts/dates/provisions. (11)
- **Generative LLM (decoder) + RAG** — Q&A, summarization, drafting, explanation. (1,6,9,10)
- **+ QLoRA SFT** — shape the cautious, cited tax "voice" and task formats.
- **+ Preference optimization (DPO/ORPO/KTO)** — penalize over-confident/uncited answers,
  reward expert-preferred ones.

---

## C. How to define the loss (per model)

This is the part that's easy to get wrong. Pick the loss to the task; **select
checkpoints on the eval gates in `05`, not on the training loss.**

### 1) Embeddings / retriever (bi-encoder)
- **Multiple-Negatives Ranking Loss (MNRL) = in-batch InfoNCE/NT-Xent.** For a batch of
  (query, positive) pairs, maximize cosine(q, p⁺) vs. all other in-batch passages as
  negatives; temperature τ. *The workhorse.*
- **Add mined hard negatives** — passages that are lexically/semantically close but the
  *wrong* provision (e.g., a different but related IT). This is the single biggest quality
  lever for a tax retriever, because the failure mode is "near-miss provision."
- Alternatives: **triplet margin loss** (anchor/pos/neg); **CoSENT / cosine-MSE** when you
  have *graded* similarity labels.
- *Loss intuition:* "rank the right paragraph above plausible look-alikes."

### 2) Reranker (cross-encoder)
- **Pointwise:** binary cross-entropy on (query, passage)→relevant/not.
- **Pairwise (RankNet):** logistic loss on score差 between a relevant and a non-relevant
  passage for the same query → optimizes *ordering*.
- **Listwise (ListMLE / LambdaLoss):** optimizes the whole ranked list / nDCG directly.
- Train on the bi-encoder's top-k as candidates (realistic hard negatives).

### 3) Classifier heads
- **Multi-class** (doc routing, objection grounds): **softmax cross-entropy.**
- **Multi-label** (provision tagging — a doc can hit *many* ITA sections):
  **binary-cross-entropy-with-logits (sigmoid per label)**; add **focal loss** + class
  weighting for the long tail of rare provisions. Metric: micro/macro-F1, per-label PR.
- **Risk scoring** (ordinal): ordinal regression or calibrated multi-class; report AUC +
  calibration (ECE), since a *score* must be trustworthy.

### 4) Token classification / NER (amounts, dates, provision refs)
- **Token-level cross-entropy over BIO tags**; optional **CRF** layer for tag-sequence
  consistency. Or constrained-decoding structured output from an LLM (JSON schema) when
  spans are messy.

### 5) Entailment / contradiction (consistency checker, #8)
- **3-way cross-entropy** (entail / neutral / contradict) on a cross-encoder over
  (claim, CRA-position) pairs.

### 6) Generative SFT (Q&A, summarization, drafting)
- **Causal-LM cross-entropy (next-token), with the loss masked to the completion** — never
  train on the prompt tokens. Grounding/citation behavior comes from the *data
  construction* (every target answer cites the chunk it was built from), not a special loss.

### 7) Preference optimization (instill caution + citation discipline)
- **DPO** — logistic loss on the log-prob-ratio gap between a *chosen* (expert-preferred,
  well-cited) and *rejected* (hallucinated/over-asserting/uncited) answer, against a frozen
  reference, scaled by β. Directly teaches "prefer the cautious cited answer."
- **ORPO** — folds the preference term into SFT (no separate reference model; cheaper).
- **KTO** — needs only pointwise good/bad labels (much easier to collect from reviewer
  thumbs-up/down) instead of paired comparisons.

### 8) Optional / advanced
- **Sequence-level distillation (KL/CE to a teacher):** make a small local model *act
  senior* by imitating a strong teacher's outputs — but keep **facts in RAG**, distill
  *behavior* only.
- **RAG-marginalized training (RAG-Sequence/Token):** jointly optimize generation over
  retrieved docs; research-grade, usually unnecessary vs. training components separately.
- **Abstention/calibration:** not a fancy loss — add abstain examples to SFT and tune the
  reranker-score **threshold** on a dev set via ECE/selective-prediction curves.

---

## D. Training data — built from the two sources (and how)

| Model | Positive pairs / labels | How to construct (from the corpus) | Negatives |
|---|---|---|---|
| Embeddings | (question, gold paragraph); (paragraph, its summary); (ITA-section text, IT paragraph interpreting it) | Mine ITs (interpretive) into Q→paragraph; LLM-draft then **human-verify** | **Hard negatives**: sibling paragraphs, related-but-wrong ITs (BM25/ANN-mined) |
| Reranker | (query, passage, relevance) | Reuse embedding pairs; label bi-encoder top-k | Bi-encoder top-k non-relevants |
| Doc classifier | doc → type | Weak/heuristic labels + human audit on a sample | n/a (softmax) |
| Provision tagger | text → {ITA sections} | Regex/NER the `ita_sections` already in chunk metadata as silver labels; expert-verify a slice | n/a (multi-label BCE) |
| NER | token → BIO | Programmatic spans (regex for $amounts/dates/"subsection 20(1)(c)") + human correction | n/a |
| NLI / consistency | (claim, position) → entail/neutral/contradict | Pair draft statements with IT/Folio paragraphs; auto-generate contradictions, **human-verify** | n/a |
| Generator SFT | (instruction, cited answer) | Grounded Q→A over chunks; summaries of ITs/manual sections; drafting exemplars | n/a (masked CE) |
| Preference (DPO/KTO) | chosen vs rejected (or good/bad) | Reviewer edits/ratings from the human-in-the-loop loop in `04`; rejected = hallucinated/over-asserting variants | n/a |

**Hard rules** (from `04-evaluation.md`): every silver/synthetic label is **human-verified
before promotion**; training and eval items must come from **disjoint** documents to avoid
leakage; keep a frozen gold test set the models never train on.

---

## E. Worked example — flagship "cited research + audit-technique" assistant

End-to-end, concrete:

1. **Embeddings** (fine-tuned bge, **MNRL + hard negatives**) → ANN index over chunks.
2. **BM25** over the same chunks → hybrid candidate set.
3. **Reranker** (bge cross-encoder, **pairwise/listwise**) → top-k.
4. **Generator** (Qwen2.5/Llama-3.x via vLLM) under the citation contract (`02`),
   **QLoRA-SFT** for the cautious cited voice, **DPO/KTO** on reviewer feedback.
5. **Guardrails** (`02`): cite-verify (→ fabricated-citation rate 0), currency flag,
   authority disclaimer, abstain-on-low-score.
6. **Eval** (`04`/`05`): retrieval Recall@10 ≥ 0.90; faithfulness ≥ 0.95;
   currency-flagging ≥ 0.95; human expert pass ≥ 0.90, 0 materially-wrong.

Each component has its own loss and its own metric; the product is graded by the
end-to-end acceptance gates. That separation is what makes the system measurable,
debuggable, and safe to iterate.
