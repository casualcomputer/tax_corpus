# 09 — Working, proven reference implementations (GitHub)

Authoritative, actively-maintained, end-to-end code you can run to implement each part of
this design. Grouped by stage; ⭐ = battle-tested / widely used; 🏃 = one-command or
notebook-runnable end-to-end.

## LLM fine-tuning (SFT / QLoRA) — end-to-end, runnable

- 🏃⭐ **Unsloth** — `github.com/unslothai/unsloth`. Fastest single-GPU QLoRA; official
  **Colab notebooks** that train Llama/Qwen/Mistral end-to-end and export GGUF. Best
  "prove it works today" path.
- 🏃⭐ **LLaMA-Factory** — `github.com/hiyouga/LLaMA-Factory` (ACL 2024). Config/YAML- and
  WebUI-driven SFT / QLoRA / DPO / ORPO / KTO across 100+ models. One YAML → trained model.
- ⭐ **Axolotl** — `github.com/axolotl-ai-cloud/axolotl`. Config-driven, reproducible,
  production-grade fine-tuning pipelines.
- ⭐ **Hugging Face TRL** — `github.com/huggingface/trl`. The reference trainers
  (`SFTTrainer`, `DPOTrainer`, `ORPOTrainer`, `KTOTrainer`) with runnable
  `examples/scripts/` (`sft.py`, `dpo.py`, `kto.py`, …). This is the canonical
  implementation of the **losses** in `07`.
- ⭐ **PEFT** — `github.com/huggingface/peft`. LoRA/QLoRA building blocks (used by all above).

> Preference optimization (the "make it cautious & cited" step in `07`) is just the
> DPO/ORPO/KTO trainers in TRL / LLaMA-Factory — same code, different dataset (chosen vs
> rejected answers from your reviewer feedback loop).

## Embeddings & reranker fine-tuning — the retrieval losses in `07`

- 🏃⭐ **sentence-transformers** — `github.com/UKPLab/sentence-transformers`. Reference
  training for **bi-encoders** (`MultipleNegativesRankingLoss` = InfoNCE, `TripletLoss`,
  `CoSENTLoss`) and **cross-encoder rerankers**; runnable scripts under
  `examples/.../training/` (incl. `cross_encoder/training/rerankers/`).
- ⭐ **FlagEmbedding (BGE)** — `github.com/FlagOpen/FlagEmbedding`. End-to-end **embedder +
  reranker fine-tuning**, plus a **hard-negative mining** script and an evaluation suite —
  exactly the recipe in `07`/`03`.
- ⭐ **Tevatron** — `github.com/texttron/tevatron`. Clean dense-retrieval training toolkit
  (DPR-style, contrastive + hard negatives).
- ⭐ **ColBERT** — `github.com/stanford-futuredata/ColBERT` and **RAGatouille**
  `github.com/AnswerDotAI/RAGatouille`: late-interaction retrieval, easy to fine-tune.

## RAG-aware fine-tuning (combine retrieval + SFT)

- ⭐ **RAFT** — `github.com/ShishirPatil/gorilla` (`/raft`). Reference recipe to train a
  model to **cite the right passage and ignore distractors** — the "light citation SFT."
- ⭐ **Self-RAG** — `github.com/AkariAsai/self-rag`. Training + inference for
  reflection/critique tokens → on-demand retrieval, citation, and abstention.

## RAG application frameworks (serving stack in `02`)

- ⭐ **LlamaIndex** — `github.com/run-llama/llama_index`. Ingestion → hierarchical chunking
  → hybrid retrieve → rerank → cited synthesis; closest to `02` out of the box.
- ⭐ **Haystack** — `github.com/deepset-ai/haystack`. Production pipelines, strong on hybrid
  retrieval + evaluation.
- ⭐ **LangChain** — `github.com/langchain-ai/langchain`. Ubiquitous; many RAG templates.
- ⭐ **txtai** — `github.com/neuml/txtai`. Lightweight all-in-one embeddings DB + RAG.
- ⭐ **GraphRAG** — `github.com/microsoft/graphrag`. If you later want cross-document
  reasoning over the corpus.

## Local serving (keep it on-prem)

- ⭐ **vLLM** — `github.com/vllm-project/vllm` (GPU, AWQ/GPTQ, OpenAI-compatible API).
- ⭐ **llama.cpp** — `github.com/ggml-org/llama.cpp` (CPU/Metal, GGUF).
- ⭐ **Ollama** — `github.com/ollama/ollama` (simplest local model runner).
- ⭐ **TGI** — `github.com/huggingface/text-generation-inference`.

## Evaluation harnesses (the gates in `04`/`05`)

- ⭐ **RAGAS** — `github.com/explodinggradients/ragas` (faithfulness, answer/context metrics).
- ⭐ **DeepEval** — `github.com/confident-ai/deepeval` (assertion-style tests, CI regression).
- ⭐ **TruLens** — `github.com/truera/trulens` (RAG tracing + feedback functions).
- ⭐ **ARES** — `github.com/stanford-futuredata/ARES` (automated RAG eval).
- ⭐ **RAGTruth** — `github.com/ParticleMedia/RAGTruth` (hallucination corpus; **train a
  small word-level hallucination detector** for the faithfulness gate).
- ⭐ **promptfoo** — `github.com/promptfoo/promptfoo` (prompt/model A/B on the gold set).
- ⭐ **BEIR** — `github.com/beir-cellar/beir` & **MTEB** —
  `github.com/embeddings-benchmark/mteb` (retrieval/embedding benchmarking).

## Domain exemplars (regulated-domain end-to-end, to imitate)

- ⭐ **LegalBench** — `github.com/HazyResearch/legalbench` (incl. the **SARA tax** tasks).
- **SARA (tax)** — `github.com/SgfdDttt/sara` · data `jhu-clsp/SARA`.
- **COLIEE solution (CAPTAIN)** — `github.com/Nguyen2015/CAPTAIN-COLIEE2023`: a complete,
  competitive **legal retrieval + entailment** pipeline you can adapt to ITs/Folios.
- **SaulLM** — models `Equall/Saul-7B-Instruct-v1` (HF): a legal LLM built with the exact
  pretrain→SFT→DPO recipe in `01`.
- ⭐ **FinGPT** — `github.com/AI4Finance-Foundation/FinGPT`: open, end-to-end domain LLM
  (RAG + LoRA + benchmark) in another regulated field.

## Evidence map — claim → proof

| Design claim (this repo) | Proven by (repo / paper) |
|---|---|
| RAG backbone beats parametric memory in regulated domains | MedRAG/MIRAGE; RAG; FinGPT |
| Hard-negative contrastive training for the retriever | DPR; FlagEmbedding; sentence-transformers |
| Cross-encoder reranking adds the most precision | FlagEmbedding (bge-reranker); ColBERTv2 |
| Light, citation-disciplined SFT (not fact injection) | RAFT; Self-RAG |
| Preference optimization for caution/citation | TRL DPO/ORPO/KTO; SaulLM (DPO) |
| Pretrain→SFT→preference works in a regulated domain | SaulLM; Med-PaLM 2; BloombergGPT |
| Faithfulness/hallucination must be measured & gated | RAGAS; ARES; RAGTruth; FActScore |
| Task-typed, expert-built gold sets | LegalBench; SARA; MultiMedQA |
| QLoRA makes local fine-tuning feasible | QLoRA; Unsloth; LLaMA-Factory; Axolotl |

Suggested first run (proves the whole loop on a laptop/single GPU): **Unsloth notebook**
(SFT a 7–8B model on a few hundred corpus-grounded Q→A) → serve via **Ollama/vLLM** →
wrap with **LlamaIndex** hybrid retrieval + **bge-reranker** → grade with **RAGAS** +
the custom tax metrics in `04`.
