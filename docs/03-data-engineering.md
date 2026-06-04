# 03 — Data engineering for the two CRA sources

The corpus is the product. Retrieval quality is capped by chunking + metadata quality.

## A. Acquisition

- Crawl the two index pages, enumerate every **Interpretation Bulletin** and every
  **Audit Manual** chapter, fetch each.
- Persist **raw HTML** plus `source_url` and `retrieved_at` (UTC). Raw HTML is your
  audit trail and lets you re-parse without re-crawling.
- Be polite: throttle, cache, honor robots. See licensing in `06-tax-domain-notes.md`
  (CRA content is Crown copyright; non-commercial reproduction is generally permitted
  with source attribution — confirm for your use case).
- **Bilingual note:** CRA publishes EN + FR. English-only is a fine MVP; bilingual
  retrieval is a real differentiator and a later milestone (store `language`).

## B. Parsing (structure-aware — this is where most teams lose quality)

Convert HTML → clean text **while preserving structure**:

- **Headings & hierarchy** (chapter → section → subsection).
- **Numbered paragraphs.** ITs are organized into numbered paragraphs; **these numbers
  are the citation unit.** Capture them as `paragraph_id`. Losing them makes precise
  citation impossible.
- **Tables, lists, footnotes, cross-references.** Keep tables as Markdown; keep "see
  paragraph 12" cross-refs.
- Strip nav/boilerplate/breadcrumbs/cookie banners.

## C. Chunking

- **Section/paragraph-aware semantic chunking**, not fixed-size sliding windows.
  - For **ITs**: chunk at the numbered-paragraph level (or small coherent groups), so a
    retrieved chunk maps to a citable paragraph.
  - For the **Audit Manual**: chunk at sub-section level; keep procedural steps intact.
- Target ~**300–800 tokens** with light overlap, but **never split across a natural
  boundary** just to hit a size.
- **Hierarchical / parent-document retrieval:** index small chunks for precision, but
  carry a pointer to the parent section so the generator gets enough context.

## D. Metadata enrichment (the differentiator for a *regulated* domain)

Every chunk carries provenance + currency + linkage (full schema:
`schemas/chunk.schema.json`):

- `source_type`: `audit_manual` | `interpretation_bulletin`
- `doc_id`: e.g. `IT-518R`, or `audit-manual/ch-11`
- `title`, `section_path`, `paragraph_id`
- `issue_date`, `last_updated`
- `status`: `current` | `archived` | `superseded`  + `superseded_by` (e.g., a Folio id)
- `ita_sections`: extracted references, e.g. `["67.1", "18(1)(a)"]`
  (regex for `subsection \d+\(\d+\)\([a-z]\)` etc., optionally a small NER pass)
- `authority_tier`: e.g. `cra_administrative_position` | `cra_internal_procedure`
- `source_url`, `retrieved_at`, `language`, `content_hash`

`status` + `issue_date` are what let the system **refuse to present an archived IT as
current law** — a core safety property, not a nicety.

## E. Indexing

- **Dense:** embed chunks with a local model; store vectors + full metadata.
- **Sparse:** BM25 over the same chunks.
- **Filters:** enable metadata filtering at query time (e.g., exclude `archived` unless
  the user explicitly asks for historical positions; filter by `ita_sections`).
- **Re-index on source change:** when CRA updates a Folio/manual chapter, re-fetch →
  re-parse → re-embed only the changed docs (`content_hash` diff). This is how you keep
  currency without retraining anything.

## F. Mining the corpus for SFT + eval data (reuse the same pipeline)

- ITs are interpretive → turn each into **Q→A pairs** grounded in their own paragraphs.
- Audit Manual → "what does CRA look for when auditing X?" procedural Q→A.
- Use a strong model to **draft**, then **human-verify** a sample before anything becomes
  gold/training data (never ship unverified synthetic gold — see `04-evaluation.md`).
