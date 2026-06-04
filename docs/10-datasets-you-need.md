# 10 — Datasets you need (reuse + build), with finance/tax/accounting literature

Two buckets: **(A) existing public datasets** to reuse for transfer-learning, capability
testing, and method validation; **(B) datasets you must build** from the CRA corpus
(nothing public is *Canadian-income-tax-correct*). Plus **(C)** the academic literature
that shapes the design.

> ⚠️ **Jurisdiction caveat.** The public tax/finance/accounting sets below are US, Brazil,
> Germany, China, etc. They are excellent for **methodology, capability, and robustness
> testing** and as **construction templates**, but their *content* is **not Canadian law**
> — they do **not** replace your own Canadian gold set (B). Also check each dataset's
> **license** before any non-research use.

---

## A. Existing public datasets to reuse

### Tax-specific (closest to the goal)
| Dataset | What it is | Why it matters here |
|---|---|---|
| **SARA** (Holzenberger 2020, arXiv:2005.05257) | US tax-code **entailment + QA** | Template for "does this provision apply to these facts?"; in LegalBench. |
| **BR-TaxQA-R** (arXiv:2505.15916) | 715 Qs from Brazil's 2024 IRS Q&A + statutes + **administrative rulings**, **with references** | Near-exact analog of your goal: **QA-with-citations over tax authority + rulings.** Best construction template. |
| **SteuerLLM / SteuerEx** (arXiv:2602.11081) | **Local** German tax-law LLM + 115 expert-validated exam Qs over 6 tax domains | Direct precedent for a **local, specialized tax LLM** + an expert-validated eval set. |
| **TaxPraBen** (arXiv:2604.08948) | Chinese real-world **tax-practice** benchmark | Structured eval over practical tax tasks (not just exams). |
| **"Can LLMs Identify Tax Abuse?"** (arXiv:2508.20097) | Tax-avoidance/abuse detection | Maps to the **audit/compliance** use cases (#5/#6) from the Audit Manual. |
| **Logic-Programs for Tax Reasoning** (arXiv:2508.21051) | Neurosymbolic tax computation | Template for **computational** answers where a wrong number is unacceptable. |

### Accounting & auditing
| Dataset | What it is | Why it matters here |
|---|---|---|
| **AuditBench** (Springer 2025) | Financial-statement **auditing** benchmark, 5-stage eval | Analog for audit-procedure reasoning; shows LLMs **fail to cite standards** → validates our citation gate. |
| **Kuaiji** (arXiv:2402.13866) | First Chinese **accounting** LLM + CPA-based dataset | End-to-end domain-LLM exemplar (CPA syllabus incl. tax law). |
| **IDEA-FinBench** | **CFA/CPA** exam Qs, 16 subjects, bilingual | Off-the-shelf professional-exam capability probe. |
| **"Automating Financial-Statement Audits with LLMs"** (arXiv:2506.17282) | Error-detection over transactions | Evidence on LLM audit limits (explanation/citation gaps). |

### Finance (numerical reasoning, retrieval, IE — strong method transfer)
| Dataset | What it is | Why it matters here |
|---|---|---|
| **FinQA** (arXiv:2109.00122) / **ConvFinQA** (2210.03849) | Numerical reasoning over filings (single / multi-turn) | Templates for **computational** answer_type + conversational follow-ups. |
| **TAT-QA** (arXiv:2105.07624) / **MultiHiertt** | **Table+text** QA over financial reports | Tables appear in the Audit Manual; same hybrid reasoning. |
| **FinanceBench** (arXiv:2311.11944) | 10,231 Qs over **real filings with evidence strings** | The **open-book RAG eval** template (answer **+ evidence**) — mirror this format for ITs/manual. |
| **FinBen** (arXiv:2402.12659) | 36 datasets / 24 tasks incl. **RAG + agent** eval | Blueprint for a *holistic* benchmark structure. |
| **BizBench** (arXiv:2311.06602) | Quantitative reasoning via **program synthesis** + **SEC-Num** extraction | Supports tool-use/program-synthesis for safe tax math; IE template. |
| **EDGAR-CORPUS** (arXiv:2109.14394) + **EDGAR-CRAWLER** | Large 10-K corpus + scraper | Reference for clean **corpus-construction** at scale. |
| **Loughran-McDonald** lexicon (2011) | Finance textual-analysis dictionary | Lightweight domain lexicon (term weighting / sparse features). |

### Legal & RAG/eval (cross-cutting — see also `08`)
- **LegalBench** (`nguha/legalbench`), **COLIEE** (statute retrieval+entailment),
  **LexGLUE**, **CUAD**, **ContractNLI** — task templates for entailment/extraction.
- **RAGTruth** (train a hallucination detector), **RAGAS/ARES** (faithfulness),
  **BEIR/MTEB** (retrieval/embedding selection), **FActScore** (claim factuality).

---

## B. Datasets you must build (from the CRA corpus — the part that's actually Canadian)

Construction methods are in `03`/`04`; schemas in `schemas/`. Targets are starting points.

| Purpose | Model it serves | Format | Target size | How to build |
|---|---|---|---|---|
| **Retrieval pairs** | Embeddings (`07` InfoNCE) | (question, gold paragraph) + **hard negatives** | 2k–10k | Mine ITs/manual → Q→paragraph; mine hard negatives (BM25/ANN). |
| **Reranker labels** | Cross-encoder | (query, passage, relevance) | 10k+ | Label the bi-encoder's top-k. |
| **SFT instructions** | Generator QLoRA | (instruction, **cited** answer) | 1k–5k | Grounded Q&A + summarize-IT + explain-audit-technique + **abstain** + **currency-flag** examples. |
| **Preference pairs** | DPO/ORPO/KTO | chosen vs rejected (or good/bad) | 0.5k–3k | From the reviewer feedback loop; rejected = hallucinated/over-asserting/uncited. |
| **Provision tags** | Multi-label classifier | text → {ITA sections} | few k chunks | Silver from `ita_sections` regex; expert-verify a slice. |
| **NER spans** | Token classifier | BIO (amounts/dates/§refs) | 0.5k–2k | Programmatic spans + human correction. |
| **Gold eval QA** | End-to-end gates | `eval_item.schema.json` | **200–1,000** | Expert-authored/validated; task-typed; `required_citations` + `relevant_chunk_ids`. |
| **Red-team set** | Safety gates | `eval_item.schema.json` | 100–300 | 5 categories: outdated_position, out_of_scope, hallucination_bait, authority_confusion, ambiguous_facts. |

**Non-negotiables (from `04`):** human-verify every silver/synthetic label before
promotion; keep **train/eval document-disjoint**; freeze a gold test set the models never
train on; mirror the **answer-with-evidence** format proven by BR-TaxQA-R / FinanceBench.

---

## C. What the finance/tax/accounting literature tells us (and how it changes the design)

1. **"Answer + references" is the validated format.** BR-TaxQA-R and FinanceBench both pair
   answers with evidence/citations — exactly our citation contract (`02`). Build your gold
   set the same way.
2. **A local, specialized tax LLM is a proven pattern.** SteuerLLM (German) and Kuaiji
   (Chinese accounting) show the local-domain-LLM route works — and that an
   **expert-validated** eval set is standard practice (`05`).
3. **LLMs are weak at numerical/statutory computation.** FinQA/ConvFinQA/BizBench and the
   tax logic-program work show raw LLMs miscompute. → For `computational` answers, use
   **tool-use / program synthesis / a calculator**, not free-form generation.
4. **LLMs over-rely on surface phrasing, not legal reasoning** (Hu et al. 2025). → Include
   **paraphrase-robustness** and **adversarial** items in eval (`04`).
5. **Models detect issues but fail to cite the governing standard** (AuditBench;
   financial-audit work). → Our **fabricated-citation = 0** and **authority-framing** gates
   are exactly the right gates (`05`).
6. **Holistic, multi-task benchmarks are the norm** (FinBen, LegalBench). → Structure the
   Canadian gold set by **task type** (factual / interpretive / procedural / computational /
   out-of-scope), not as one undifferentiated QA blob.
7. **Domain pretrain → SFT → preference works in regulated fields** (SaulLM, Med-PaLM 2,
   BloombergGPT). → Confirms the `01` sequence; do it **only if** RAG+light-SFT plateaus.

**Bottom line:** reuse A for capability/robustness testing and as construction templates;
invest your real effort in B (the Canadian gold + training sets); let C's findings set the
guardrails. None of the public sets are Canadian-tax-authoritative — that gap *is* your moat.
