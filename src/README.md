# tax_corpus engine (`src/taxcorpus/`)

Stdlib-only core so it runs anywhere; canada.ca-specific selectors get finalized once we
have real HTML/PDF samples.

| Module | Role |
|---|---|
| `ingest.py` | structure-aware HTML → paragraph-anchored chunks (`schemas/chunk.schema.json`); provision extraction; doc-level currency (`archived`/`superseded`) inference. |
| `guardrails.py` | the anti-Blue-J layer: **cite-verify** (drop any citation not in the retrieved set → fabricated-citation rate 0), **currency caveat**, **abstention**, standing disclaimer. |
| `eval_harness.py` | the `docs/05` gates that need no model: recall@k, citation precision, currency-flagging, abstention; pluggable faithfulness scorer (lexical fallback offline). |
| `fetch.py` | fetch with a **local-drop fallback** — reads pre-downloaded sources from `data/corpus/source/` when the network is blocked (this environment blocks canada.ca). |

## Prove it (no network)
```bash
python3 scripts/demo_pipeline.py
```
Runs the full chain on a synthetic Interpretation Bulletin and asserts: paragraph anchors
kept, provisions + superseded status extracted, a **fabricated citation dropped**, the
**currency warning fired**, abstention on low confidence, and a green eval scorecard.

## Getting real data in (network is blocked here)
Pick one, then run ingestion:
1. **Change the environment network policy** to allow `canada.ca`, then `fetch.fetch_url(...)`.
2. **Drop downloaded files** into `data/corpus/source/` → `fetch.iter_drop()` reads them.
3. **Run ingestion where the network is open** and commit the parsed `chunks` back.

## Not yet built
PDF/forms parser (for the CRA forms stream — `parse_pdf` with AcroForm field extraction),
the embedding/reranker training wiring (uses `data/derived/` triplets), and the local-LLM
RAG loop (the generator behind the guardrails).
