# Taxonomy coverage report

- Tax terms: **77**  |  Acronyms: **158** (merged as altLabel: 0, grouped: 158)
- Nodes: **35** across facets: subject_matter 10, process_stage 7, taxpayer_type 7, authority_tier 3, program_entity 8
- Tax terms with a subject-matter placement: **77/77**
- Tax terms with a model-proposed provision (SME to verify): **63/77**

## Largest nodes (watch for over-broad buckets)
- `pe-other` (Other program acronyms (triage)): 28
- `pe-org` (Organizational units): 26
- `pe-document` (Manuals, reports & forms): 19
- `pe-system` (Systems & tools): 18
- `pe-role` (Roles & specialists): 18
- `ps-audit` (Audit & examination): 14
- `sm-gst-hst` (GST/HST): 13
- `pe-sred` (SR&ED program concepts): 13
- `sm-registered-plans` (Registered & savings plans): 12
- `sm-capital` (Capital gains & property): 11
- `sm-business-accounting` (Business & accounting concepts): 11
- `tt-individual` (Individual): 9

## SME-review queue

- **Unplaced tax terms (need a subject node):** none
- **All placements & provisions are `validated:false`** (method=llm/skeleton) — confirm before use.
- **GST/HST provisions cite the Excise Tax Act (ETA)**, not the ITA — verify.
- **`pe-other`** holds uncategorized program acronyms — triage into a facet.
- Overloaded initialisms (e.g., ITC = Input tax credit vs Investment tax credit; AD) kept as distinct terms.
