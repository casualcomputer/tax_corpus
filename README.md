# tax_corpus — Teaching a local LLM Canadian income-tax domain knowledge

A reference design + methodology for making a **locally-hosted LLM** competent on
Canadian income-tax material, starting from two CRA sources:

- **Income Tax Audit Manual** (Domestic Compliance Programs Branch / DCPB) — CRA's
  internal *procedural* guidance for auditors.
- **Income Tax Interpretation Bulletins (ITs)** — CRA's *administrative interpretation*
  of specific Income Tax Act (ITA) provisions.

> ⚠️ **Read `docs/06-tax-domain-notes.md` first.** Interpretation Bulletins are
> **not law**, most have been **archived and superseded by Income Tax Folios** since
> 2013, and the Audit Manual is *procedure*, not statutory authority. Currency,
> provenance, and authority-tier handling are first-class requirements in this design,
> not afterthoughts. This system is **decision-support, not tax advice.**

## TL;DR — the methodology in one paragraph

In a regulated, citation-heavy, frequently-changing domain like tax, **facts must be
retrieved, not memorized.** So the backbone is **Retrieval-Augmented Generation (RAG)**
with strict citation + currency enforcement. Fine-tuning (QLoRA) is used only to shape
*behavior* — the cautious, qualified, citation-disciplined "voice" of a tax answer and
the specific task shapes — **not** to inject facts (memorized tax facts go stale and
can't be cited). Continued/domain-adaptive pre-training is optional and only pays off at
scale. Success is measured on a purpose-built **gold QA + retrieval-gold + red-team**
benchmark across three axes: **retrieval quality, groundedness/faithfulness, and
tax-specific correctness** (citation accuracy, currency-flagging, authority framing,
calibrated abstention), with hard acceptance gates and human expert review.

## The decision framework (which lever for what)

| Lever | What it changes | Use it for | Do **not** use it for |
|---|---|---|---|
| **RAG / retrieval** | External knowledge index | Facts, citations, currency, provenance, auditability | — (this is the backbone) |
| **SFT / QLoRA** | Model weights (behavior) | Format, citation discipline, cautious register, task shapes, domain vocab | Injecting facts (they go stale, can't be cited) |
| **Continued pre-training (DAPT)** | Model weights (fluency) | Deep domain fluency at scale | Most teams — high cost, low marginal value vs. RAG+SFT |

**Recommended path:** RAG-first → add a light QLoRA for behavior/format/citation
discipline → consider DAPT only if a strong RAG+SFT baseline still struggles with
domain language.

## Repository map

```
docs/
  01-methodology.md                  How to "teach" the model: RAG vs SFT vs DAPT, decision logic
  02-end-to-end-design.md            Full pipeline + serving architecture (with diagram)
  03-data-engineering.md             Acquisition → parse → chunk → metadata → index, for the 2 sources
  04-evaluation.md                   Eval frameworks, test-dataset construction, metrics
  05-success-metrics.md              KPIs, acceptance gates, online monitoring
  06-tax-domain-notes.md             Authority hierarchy, IT currency, legal/usage caveats
  07-use-cases-and-modeling.md       Use-case portfolio + which model + datasets + loss functions
  08-related-publications-and-prior-art.md   Tax/legal/finance/medical prior art (the evidence base)
  09-reference-implementations.md    Working, proven GitHub repos for each stage (+ evidence map)
  10-datasets-you-need.md            Datasets to reuse vs build; finance/tax/accounting literature
  11-data-labelling-and-generation.md   Per-use-case labelling/generation process (jargon/topics/procedures)
schemas/
  chunk.schema.json        Canonical chunk record (provenance + currency + ITA refs)
  eval_item.schema.json    Gold QA / red-team item schema
data/eval/
  seed_questions.jsonl     Seed gold items (schema demonstration — expert-validation required)
requirements.txt           Recommended OSS components (local-first)
```

## What these two sources can and can't do

- **Good starting corpus:** ITs are interpretive and naturally Q→A shaped (great for
  both retrieval and SFT seed data); the Audit Manual teaches *how CRA reasons about
  compliance and risk* (net-worth assessments, indirect verification, industry audit
  techniques).
- **Insufficient alone** for a general Canadian tax assistant. Plan to add (in priority
  order): the **ITA + Regulations**, **Income Tax Folios** (which supersede the ITs),
  CRA **technical interpretations / advance rulings**, **Tax Court / FCA case law**, and
  annual **budget/legislative** changes. See `docs/06-tax-domain-notes.md`.

## Status

Design scaffold. Schemas and the evaluation methodology are concrete and usable now;
the ingestion/serving code is specified (see `docs/`) and intentionally not yet
committed as runnable modules so it can be built to your chosen stack (vLLM/Ollama,
Qdrant/pgvector, etc.).
