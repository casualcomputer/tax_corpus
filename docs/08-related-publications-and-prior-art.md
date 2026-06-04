# 08 — Related publications & prior art (tax and adjacent domains)

You don't have to invent the methodology — regulated-domain LLM work is well-trodden in
**tax, law, finance, and medicine.** This is the evidence base behind the design choices
in `01`–`07`. Datasets/benchmarks you can reuse or imitate are flagged 📊; method papers 📄.

## Tax-specific

- 📊📄 **SARA — Statutory Reasoning Assessment** (Holzenberger et al., EMNLP 2020).
  US-federal-tax statutory reasoning: **entailment + QA** over edited tax-code sections.
  Directly analogous to "does this provision apply to these facts?" Included in LegalBench
  as `sara_entailment` / `sara_numeric`. arXiv:2005.05257 · data: `jhu-clsp/SARA`,
  `github.com/SgfdDttt/sara`.
- 📄 **"Language Models and Logic Programs for Trustworthy Tax Reasoning"**
  (arXiv:2508.21051, 2025). **Neurosymbolic** tax reasoning (LLM → logic program) for
  *trustworthy, auditable* computation — the template for our **computational** answer_type
  where a wrong number is unacceptable.
- 📄 Tax administrations' own AI programs (CRA, IRS, HMRC, ATO) emphasize the same pillars
  we use: provenance, currency, human-in-the-loop, and decision-support framing.

## Law (the closest analog — same authority/citation/currency problem)

- 📊 **LegalBench** (Guha et al., NeurIPS 2023): 162 hand-built legal-reasoning tasks
  (classification, extraction, entailment, generation). The template for building our own
  task-typed gold set. arXiv:2308.11462 · `github.com/HazyResearch/legalbench` ·
  `nguha/legalbench`.
- 📊 **COLIEE** (annual): statute + case-law **retrieval (Task 3) and entailment/QA
  (Task 4)** — mirrors our retrieve-then-ground pipeline and the consistency-checker.
- 📊 **LexGLUE** (Chalkidis et al., ACL 2022, arXiv:2110.00976): legal NLU benchmark.
- 📊 **CUAD** (Hendrycks et al., NeurIPS 2021, arXiv:2103.06268): contract-clause
  **extraction** — analog for our information-extraction use case (#11).
- 📊 **ContractNLI** (Koreeda & Manning, 2021): document-level **NLI** — analog for the
  contradiction/consistency checker (#8).
- 📄 **Legal-BERT** (Chalkidis et al., 2020, arXiv:2010.02559) & **CaseHOLD / "When does
  pretraining help?"** (Zheng et al., 2021, arXiv:2104.08671): evidence on **when domain
  pretraining pays off** — informs our "DAPT is optional" stance (`01`).
- 📊 **Pile of Law** (Henderson et al., 2022, arXiv:2207.00220): 256GB legal pretraining
  corpus — the model for assembling a clean domain corpus.
- 📄 **SaulLM-7B / -54B / -141B** (Equall, 2024, arXiv:2403.03883, 2407.19584): a legal LLM
  built exactly as we recommend — **continued pretraining → legal instruction SFT →
  preference alignment (DPO).** The strongest end-to-end validation of the `01` sequence in
  a regulated domain.

## Finance & medicine (high-stakes, grounding-critical)

- 📄 **BloombergGPT** (Wu et al., 2023, arXiv:2303.17564): 50B finance model via mixed
  domain+general pretraining. Evidence that **DAPT at scale works but is expensive** —
  reinforces "RAG-first, DAPT only at scale."
- 📊📄 **FinGPT** (AI4Finance) & **PIXIU/FLARE**: open finance LLM with **RAG + LoRA** and a
  finance benchmark — a working open analog to our stack.
- 📄 **Med-PaLM / Med-PaLM 2** (Singhal et al., Nature 2023; arXiv:2212.13138, 2305.09617)
  with **MultiMedQA**: the canonical case for **expert human evaluation + safety framing**
  in a regulated domain — validates our human-review acceptance gate (`05`).
- 📊 **MIRAGE / MedRAG** (Xiong et al., 2024, arXiv:2402.13178): medical RAG benchmark
  showing **retrieval beats parametric memory** in a regulated field — the core RAG thesis.

## RAG methods & evaluation (the backbone + how to grade it)

- 📄 **RAG** (Lewis et al., NeurIPS 2020, arXiv:2005.11401) and **Fusion-in-Decoder**
  (Izacard & Grave, 2021, arXiv:2007.01282): foundations.
- 📄 **Self-RAG** (Asai et al., ICLR 2024, arXiv:2310.11511): self-reflective retrieval +
  critique tokens → on-demand retrieval, citation, and **abstention** (our guardrails).
- 📄 **RAFT — Retrieval-Augmented Fine-Tuning** (Zhang et al., 2024, arXiv:2403.10131):
  train the model to **cite the right passage and ignore distractors** — direct evidence
  for "RAG + a light, citation-disciplined SFT" (`01`,`07`).
- 📊📄 **RAGAS** (arXiv:2309.15217), **ARES** (arXiv:2311.09476): automated RAG metrics
  (faithfulness, answer/context relevancy) — our `04` harness.
- 📊 **RAGTruth** (Niu et al., ACL 2024, arXiv:2401.00396): 18k word-level hallucination
  annotations; **fine-tune a small detector** to power our faithfulness/cite-verify gate.
- 📄 **FActScore** (Min et al., 2023, arXiv:2305.14251): atomic-claim factuality — a model
  for our claim-level groundedness metric.

## Retrieval / embeddings / PEFT / preference (the component losses)

- 📄 **DPR** (Karpukhin et al., 2020, arXiv:2004.04906): dense retrieval with **in-batch +
  hard negatives** — the basis of our embeddings loss (`07`).
- 📄 **Contriever** (Izacard et al., 2022, arXiv:2112.09118): contrastive retrieval.
- 📄 **E5** (2212.03533) and **BGE / C-Pack** (2309.07597): strong open embeddings to
  fine-tune from.
- 📄 **ColBERTv2** (Khattab et al., 2021, arXiv:2112.01488): late-interaction retrieval.
- 📊 **BEIR** (2104.08663) and **MTEB** (2210.07316): pick/validate the base embedding model.
- 📄 **"Don't Stop Pretraining" (DAPT/TAPT)** (Gururangan et al., ACL 2020,
  arXiv:2004.10964): the evidence base for the DAPT decision.
- 📄 **LoRA** (2106.09685) and **QLoRA** (2305.14314): the PEFT we use for behavioral SFT.
- 📄 **DPO** (2305.18290), **ORPO** (2403.07691), **KTO** (2402.01306): the preference-loss
  menu in `07`.

## Commercial & community prior art (Canadian tax AI) — yes, this is being built

Two cohorts, and both converge on *exactly* this repo's design — **RAG over authoritative
Canadian sources + mandatory citations + human review**:

- **Commercial, professional-grade:**
  - **Blue J** (CPA Canada partner) — generative tax research with a ChatGPT-like UI
    grounded in *primary authoritative content* + Tax Notes/IBFD, cited answers.
  - **TaxGPT (Canada)** — grounded on the ITA, CRA guidance, Tax Court, all provinces,
    GST/HST, SR&ED; **every answer carries citations**; client-document upload = RAG over a
    file.
  - **CloudTax**, plus consumer custom GPTs ("Canada Tax GPT") at the DIY end.
- **Community (r/cantax & practitioners):** heavy use of general ChatGPT — and heavy burns.
  The documented failure modes map 1:1 to our gates:

  | Reported real-world failure | Our gate (`docs/05`) |
  |---|---|
  | Hallucinated a 2026 capital-gains limit "increase" not in legislation/CRA/Finance | currency-flagging + **fabricated-citation = 0** + faithfulness |
  | Claims US deferrals apply in Canada (jurisdiction bleed) | out-of-scope / jurisdiction **abstention** (red-team) |
  | 50% of accountants saw businesses harmed; 44% spend ≤3 hrs/mo fixing AI errors | **human-in-the-loop**; decision-support, not advice |

**The consensus differentiator** everyone reaches: *narrow to authoritative Canadian
sources + cite everything + keep a human in the loop.* That is this repo's thesis.

**Where a local/DIY build still wins** (don't try to rebuild Blue J's licensed corpus):
data **privacy / on-prem** (taxpayer data never leaves the box), **cost** (no per-seat), and
**internal use cases the research tools don't target** — audit-risk triage and procedure
recommendation from the **Audit Manual**, document routing, provision tagging. The premium
tools' moat is licensed case-law/commentary breadth; compete on *your* private data and
internal compliance workflows, not on republishing authority.

## Takeaway

Every lever in this repo — RAG backbone, hard-negative embedding training, light
citation-disciplined SFT, preference alignment for caution, task-typed gold sets, expert
review, hallucination/faithfulness gating — has **published precedent and, usually, working
code** (see `09-reference-implementations.md`). The novel work is the **tax-specific
glue**: authority tiers, IT currency/supersession, and the safety gates.
