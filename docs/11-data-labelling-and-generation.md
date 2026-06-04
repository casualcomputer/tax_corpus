# 11 — Data labelling & generation, per use case

Enterprise tax data is dense with **topics, jargon, and procedures**. The way to make
labelling tractable across all use cases is to build **three reusable foundational assets
first**, then drive every per-task labelling/generation process from them. This doc covers
(A) those foundations, (B) the labelling toolkit, (C) governance, and (D) the concrete
process for each of the 12 use cases in `07-use-cases-and-modeling.md`.

---

## A. Three foundational assets (build once, reuse everywhere)

These directly tackle "lots of topics, jargon, and procedures."

1. **Domain glossary / controlled vocabulary** — tax jargon, acronyms (CCA, ACB, UCC,
   RDTOH, CDA, GAAR, arm's length, superficial loss…), and **provision-reference grammar**
   (`paragraph 20(1)(c)`, `subsection 95(2)`, `clause 110(1)(d)(ii)`). Sources: the ITs,
   Audit Manual, CRA glossary pages, and SME input. Used as: normalization map, annotation
   aid, weak-supervision **labeling functions**, query expansion for retrieval, and model
   features. Versioned like code.
2. **Topic taxonomy (the label space)** — a hierarchical set of issues/topics. Bootstrap
   from corpus structure (IT subject index, Audit Manual chapter/section titles) + **topic
   modelling** (embeddings → clustering / BERTopic) + **SME curation**. This *is* the label
   set for routing/tagging/triage (#3, #4, #12).
3. **Procedure catalog** — structured audit/processing procedures extracted from the Audit
   Manual (net-worth method, deposit analysis, ratio/markup analysis, indirect
   verification…), each with triggers, inputs, and steps. This *is* the target space for
   the recommender/triage tasks (#5, #6).

> Without these, every annotator re-learns the jargon and labels inconsistently. With them,
> labelling becomes "apply the vocabulary/taxonomy/catalog," and inter-annotator agreement
> jumps.

## B. The labelling/generation toolkit (six methods, mixed per task)

- **Programmatic / heuristic** — regex & dictionaries (provision refs, $amounts, dates,
  form numbers). Cheap, high-precision for structured signals.
- **Weak supervision** — write *labeling functions* (glossary/regex/heuristics), combine
  with a label model (Snorkel-style) → **silver labels** at scale.
- **LLM-assisted pre-labelling** — a strong model drafts labels/answers **grounded in a
  specific chunk**; humans verify/correct. The "draft → verify" pattern; 5–10× faster than
  from-scratch.
- **Active learning** — prioritize the most *uncertain/representative* items for human
  labelling (huge for the long tail of rare provisions).
- **Synthetic generation** — generate Q/A, paraphrases, and contradictions from chunks,
  with provenance recorded; **always human-verify before promotion to gold/training**.
- **Expert authoring** — SMEs (CPAs / tax lawyers / auditors) author the **gold** sets and
  adjudicate disagreements.

Tools: **Label Studio / Prodigy / Argilla / doccano** (annotation UIs), **Snorkel** (weak
supervision), the project generator (LLM pre-labelling), `modAL`/`small-text` (active
learning). Annotation records carry: `annotator`, `method` (manual|weak|llm|synthetic),
`confidence`, `source_chunk_id`, `validated`, `timestamp`.

## C. Governance (non-negotiable)

- **SME-in-the-loop + a written codebook** per task; calibration rounds; measure
  **inter-annotator agreement** (Cohen's/Fleiss' **κ ≥ ~0.7** before trusting labels);
  adjudicate conflicts.
- **Train/eval document-disjoint**; freeze a gold test set models never train on.
- **PII / privacy:** scrub taxpayer identifiers from any enterprise data used for training;
  segregate taxpayer-specific data from the public corpus; access controls + audit logs.
- **Bias:** for outcome-labelled tasks (#5, #12) beware **selection bias** (only audited/
  objected cases have outcomes) — use propensity weighting / semi-supervised methods and
  temporal (past→future) validation.

---

## D. Per use case (Input → Target → Process → QC & jargon → Volume)

### 1. Interpretive Q&A / research assistant — *SFT pairs + gold*
- **Input → Target:** corpus chunk → (question, **cited** answer, answer_type, abstain?).
- **Process:** LLM drafts a question from each IT paragraph / audit section ("grounded
  self-instruct"); LLM drafts an answer **constrained to that chunk** with citation; mine
  real practitioner FAQs and map onto the corpus; **SME edits to gold**.
- **QC & jargon:** reject answers not entailed by the cited chunk; expand questions with
  glossary jargon/acronym variants so the model sees real phrasing. **Vol:** 1–5k SFT, 200–1k gold.

### 2. Semantic search — *retrieval pairs*
- **Input → Target:** (query, relevant passage) positives + **hard negatives**.
- **Process:** reuse #1's Q→paragraph; add title/section→body and paraphrase pairs; once
  live, mine **click/feedback logs** as implicit labels. Hard negatives via BM25/ANN
  (sibling paragraphs, related-but-wrong IT) **and glossary-confusable terms** (capital vs
  current expense; salary vs dividend).
- **QC & jargon:** verify hard negatives are truly non-relevant; include **jargon↔plain-
  language** pairs so embeddings bridge the vocabulary gap. **Vol:** 2–10k.

### 3. Document classification & routing — *single-label*
- **Input → Target:** document → type (from the doc-type taxonomy: T1/T2/objection/election/
  correspondence/ruling request…).
- **Process:** **weak supervision** — labeling functions on **form numbers**, headers, and
  template phrases → label model → silver; **SME audits** a stratified sample → gold;
  active learning on the uncertain.
- **QC & jargon:** confusion-matrix review; κ on gold. Form numbers / correspondence
  templates are strong jargon signals — encode them as labeling functions. **Vol:** few k silver + ~500 gold.

### 4. Issue spotting / provision tagging — *multi-label*
- **Input → Target:** text → {ITA sections / IT numbers / topics} (multi-label).
- **Process:** **distant supervision** from `ita_sections` already extracted in chunk
  metadata and from explicit IT cross-references (a paragraph citing s.67.1 → positive for
  "67.1"); **expert-verify a slice**; active learning for **rare provisions** (long tail).
- **QC & jargon:** per-label precision/recall; enforce label **hierarchy** (subsection ⇒
  section); map jargon→provision via glossary ("superficial loss" → s.54 / 40(2)(g)).
  **Vol:** few-k chunks silver, targeted gold for rare labels.

### 5. Audit-risk triage / case selection — *outcome labels (governance-heavy)*
- **Input → Target:** taxpayer/return features → risk level / expected-adjustment.
- **Process:** use **historical audit outcomes** (enterprise data) as labels; SME defines
  risk factors; map factors → procedure catalog (RAG side). **Correct for selection bias**
  (un-audited cases lack labels → propensity weighting / semi-supervised).
- **QC & jargon:** **temporal validation**, calibration, **fairness audit**; strict PII
  scrubbing + access control. **Vol:** enterprise-history-dependent.

### 6. Audit-technique recommender — *scenario→technique*
- **Input → Target:** audit context → recommended technique(s) + **manual citation** + rationale.
- **Process:** extract the **procedure catalog** from the manual; SME authors
  scenario→technique mappings; LLM expands scenarios ("cash business, inadequate books" →
  net-worth method) **grounded in the manual**; SME (auditor) verifies.
- **QC & jargon:** auditor validation; the procedure catalog supplies the controlled
  vocabulary. **Vol:** hundreds (techniques are finite).

### 7. Authority/citation linking & currency check — *pairs + deterministic status*
- **Input → Target:** (claim/draft statement → supporting authority chunk); **currency
  status is largely a rule, not an ML label** (from `status` / `superseded_by`).
- **Process:** linking pairs from ITs' own cross-references + SME-authored statement→
  authority; build/curate the **supersession map** (IT → Folio). Hard negatives: the
  superseded version vs the current Folio.
- **QC & jargon:** SME verifies the supersession map; reranker eval on linking. **Vol:**
  reuse retrieval gold; the currency map is a curated table.

### 8. Consistency / contradiction checker — *NLI triples*
- **Input → Target:** (claim, authority) → entail / neutral / contradict.
- **Process:** SME authors a seed; **generate** contradictions by LLM perturbation (negate
  a condition, swap a **rate/dollar-limit/time-period**, flip an exception) → "contradict";
  paraphrase → "entail"; unrelated chunk → "neutral". **Human-verify** (auto-contradictions
  are noisy).
- **QC & jargon:** κ; confirm generated items are genuinely contradictory; perturb
  **domain quantities** (50% meal limit, CCA rates) for realistic, jargon-aware negatives.
  **Vol:** few-k, balanced.

### 9. Summarization — *(document, reference summary)*
- **Process:** define a summary spec (length, **must preserve citations + flag currency**);
  LLM drafts, SME edits to gold; where ITs have header/summary sections, use them as
  references.
- **QC & jargon:** faithfulness (no invented facts), coverage; **preserve precise terms**
  (don't loosely paraphrase "arm's length"). **Vol:** hundreds–1k.

### 10. Drafting assistant — *exemplars + preference pairs*
- **Process:** collect **anonymized real exemplars** (audit query letters, position
  summaries, objection responses) as targets, paired with the facts/context that produced
  them; LLM drafts, SME edits. **Preference pairs** (DPO/KTO): chosen = SME-final, rejected
  = raw draft, harvested from the **edit log**.
- **QC & jargon:** the people who write these review tone/format/citation; templates encode
  the **procedures**. Anonymize taxpayer data. **Vol:** hundreds of exemplars + edit-log pairs.

### 11. Information extraction / NER — *labelled spans*
- **Input → Target:** token → BIO spans (amount, date, **provision-ref**, tax-year,
  dollar-threshold, taxpayer-attribute, form-number).
- **Process:** **programmatic pre-annotation** (regex for $amounts/dates/provision grammar)
  → human correction in Label Studio/Prodigy → gold; or LLM **structured (JSON-schema)
  extraction** → verify. Active learning.
- **QC & jargon:** span-level F1, κ, boundary adjudication; the **provision-reference
  grammar** is the hard part — maintain a robust pattern set + dictionary of forms.
  **Vol:** 0.5–2k docs.

### 12. Objection/appeal triage — *grounds taxonomy + strength (governance-heavy)*
- **Input → Target:** objection text → ground/issue (+ optional strength/priority).
- **Process:** SME curates the **grounds taxonomy**; historical objection records →
  **silver** category labels; map grounds → provisions/authorities (RAG); strength labels
  from historical allowed/disallowed outcomes (**flag label/selection bias**).
- **QC & jargon:** κ, temporal validation; sensitive data governance. **Vol:**
  enterprise-history-dependent.

---

## Summary — primary labelling method per use case

| # | Use case | Primary method | Gold source |
|---|---|---|---|
| 1 | Interpretive Q&A | LLM-grounded generation → verify | SME edit |
| 2 | Semantic search | Reuse #1 + mined hard negatives + feedback logs | Spot-check |
| 3 | Doc routing | Weak supervision (form-number LFs) | SME audit |
| 4 | Provision tagging | Distant supervision (metadata refs) | Expert slice |
| 5 | Audit-risk triage | Historical outcomes (+debias) | Outcome data |
| 6 | Technique recommender | Procedure catalog + SME mapping | Auditor |
| 7 | Citation/currency | Cross-refs + rules (supersession map) | SME map |
| 8 | Consistency checker | LLM perturbation → verify | SME |
| 9 | Summarization | LLM draft → SME edit | SME |
| 10 | Drafting | Anonymized exemplars + edit-log preferences | Author edit |
| 11 | NER / extraction | Programmatic pre-annotation → correct | Annotator + κ |
| 12 | Objection triage | Historical records + SME taxonomy | Outcome data |

**Throughline:** build the **glossary, topic taxonomy, and procedure catalog** first; then
most labelling is **LLM/weak-supervision pre-labelling + SME verification + active learning**,
governed by κ targets, document-disjoint splits, PII scrubbing, and bias/temporal checks.
