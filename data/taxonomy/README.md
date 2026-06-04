# Induced taxonomy (from the two CRA glossaries)

Built from `data/glossary/` per `docs/12-glossary-to-taxonomy.md`. **All placements and
provisions are model-proposed (`validated: false`) — SME sign-off required before use.**

## Files
- `taxonomy.json` — SKOS-aligned nodes (`schemas/taxonomy_node.schema.json`). 35 nodes
  across 5 facets: `subject_matter`, `taxpayer_type`, `process_stage`, `authority_tier`,
  `program_entity`. Poly-hierarchy (a term can sit under several nodes).
- `coverage_report.md` — coverage / balance / SME-review queue.
- `taxonomy_tree.md` — human-readable tree with term counts + sample members.

## Inputs (also in repo)
- `data/glossary/source/*.xlsx` — the two CRA glossaries you provided.
- `data/glossary/tax_terms.jsonl` (77) and `acronyms.jsonl` (158) — normalized to
  `schemas/glossary_term.schema.json`; tax terms enriched with `synonyms` (embedded
  acronyms) and model-proposed `provisions`.

## Regenerate
```bash
pip install openpyxl jsonschema
python3 scripts/normalize_glossaries.py   # xlsx -> JSONL
python3 scripts/build_taxonomy.py         # JSONL -> taxonomy.json + reports
```

## Known review items
- **63/77** tax terms carry a model-proposed provision; **GST/HST cites the Excise Tax
  Act (ETA)**, not the ITA — verify.
- `pe-other` (28) holds uncategorized program acronyms — triage into a facet.
- Overloaded initialisms kept distinct (e.g., **ITC** = Input tax credit *vs* Investment
  tax credit; **AD** ×2).
- Provisions/placements are a **starting point for SME validation**, not authority.
