# 12 — From glossary to taxonomy

You have a glossary. Good — that's the **raw material**, not the finished label space. This
doc is exactly how the project turns it into the **topic taxonomy** that drives routing
(#3), tagging (#4), triage (#5/#12), retrieval facets (#2/#7), and human navigation.

## What "I" (this project) do, concretely

1. Define the **input contract** (`schemas/glossary_term.schema.json`) — what fields the
   builder reads from your glossary.
2. Run a **6-step build** (skeleton → embed/cluster → assign → relate → SME review →
   validate-against-use).
3. Emit a versioned, **SKOS-aligned taxonomy** (`schemas/taxonomy_node.schema.json`).
4. **Wire it into the use cases** as the label space, retrieval facets, and the bridge to
   silver-label provision tagging.

## Glossary ≠ taxonomy

| | Glossary | Taxonomy |
|---|---|---|
| Shape | flat list: term → definition (+ synonyms, cross-refs) | concepts with **broader/narrower/related**, each mapped to authority |
| Answers | "what does this term mean?" | "what bucket is this? what's near it? what governs it?" |
| Role | vocabulary | **label space** + **facet filters** + navigation |

The glossary's parts are the *inputs* to the taxonomy: **definitions** carry the semantics
you cluster on; **synonyms** become `altLabel` (your jargon-matching power); **see_also**
become `related` edges; **provisions** become the authority anchor and grouping prior.

## Four design decisions (make these before building)

1. **Poly-hierarchy / facets, not one tree.** Tax concepts have several parents — a
   *home-office expense* is both an **employment** and a **business** deduction. Use facets:
   **subject_matter · taxpayer_type · process_stage · authority_tier.**
2. **Anchor to authority.** Seed the subject-matter skeleton from the **ITA's own
   structure** (Part I → Division B → Subdivisions **a** employment / **b** business &
   property / **c** taxable capital gains / …), and map every node to ITA/Reg/IT/Folio. This
   makes the taxonomy defensible and lets it generate silver tagging labels + retrieval
   filters. Add **Audit Manual chapters** as the seed for `process_stage` nodes.
3. **Granularity follows the use case.** Routing ≈ 10–30 coarse nodes; issue/topic spotting
   ≈ 50–200; provision tagging = hundreds (≈ ITA sections). Build **one** poly-hierarchy and
   expose different "cuts."
4. **Standard = SKOS.** `prefLabel / altLabel / broader / narrower / related / definition`.
   Interoperable, and `altLabel` is exactly where your jargon variants live.

## The build pipeline (glossary → taxonomy)

0. **Normalize** the glossary to `glossary_term.schema.json` (term, definition, synonyms,
   see_also, provisions).
1. **Skeleton (top-down).** Seed ~a few dozen top-level nodes from the ITA divisions + the
   four facet axes + Audit Manual chapters. SME-blessed.
2. **Embed + cluster (bottom-up).** Embed each **term + definition** (the definition is the
   signal) with the domain embedder; **agglomerative/HDBSCAN** clustering → candidate
   groupings; an LLM **names** each cluster. Reconcile clusters against the skeleton.
3. **Assign terms (LLM-assisted, multi-label).** For each glossary term, place it under one
   or more nodes using its **definition + provisions** as evidence (terms sharing an ITA
   subdivision usually share a parent). Poly-hierarchy allowed.
4. **Extract relations from definitions.** Parse "means / is a type of / see also" + the
   provision refs → `broader/narrower` (is-a) and `related` edges. Adds depth + cross-links.
5. **SME review & adjudicate.** Card-sort/review UI; fix mis-placements; ensure **coverage**
   (every term placed) and **balance** (no 200-term catch-all). Measure κ on a sample of
   placements; only then set `validated: true`.
6. **Validate against downstream use.** Train the routing/tagging classifier on the
   taxonomy; **merge/split** nodes the model (and humans) keep confusing. Iterate. Version it.

> Automation proposes (steps 2–4); **SME disposes** (step 5). A taxonomy is a knowledge
> artifact — never ship an unreviewed one as the label space.

## Worked example (real Canadian terms → placements)

| Glossary term (synonyms) | Provision | Subject-matter parent(s) | Other facet |
|---|---|---|---|
| Adjusted cost base (**ACB**) | s.54 | Capital gains & losses | — |
| Capital cost allowance (**CCA**) | s.20(1)(a), Reg 1100 | Business & property income | related: UCC |
| Undepreciated capital cost (**UCC**) | s.13(21) | Business & property income | related: CCA |
| Superficial loss | s.40(2)(g), s.54 | Capital gains & losses | related: ACB |
| Taxable benefit | s.6(1)(a) | Employment income & benefits | — |
| Eligible dividend | s.89(1) | Corporate & dividends | taxpayer_type: shareholder |
| **RDTOH** | s.129 | Corporate & dividends | taxpayer_type: CCPC |
| Arm's length | s.251 | General / structural concepts | cross-cuts all facets |
| Net worth method | Audit Manual | Audit techniques (process) | process_stage: examination |
| Home office expense | s.8(13) **and** s.18(12) | Employment **and** Business income (**poly**) | — |

Note the two structural features: "Net worth method" lands on a **process** node (from the
Audit Manual, not the ITA), and "Home office expense" sits under **two** subject-matter
parents — that's why this is a poly-hierarchy, not a tree.

## Output & reuse

Records conform to `taxonomy_node.schema.json`. The taxonomy is then reused as:
- the **label space** for routing/tagging/triage (#3/#4/#12),
- **facet filters** + **query expansion** (via `altLabel`) for retrieval (#2/#7),
- the **silver-label bridge** for provision tagging: `glossary term → mapped_provisions →
  corpus chunks that cite those provisions` gives you distant-supervision labels (see
  `11-data-labelling-and-generation.md`, #4).

## What I need from your glossary

The fields in `glossary_term.schema.json`. Minimum: **term + definition**. Big quality
boosts if you also have **synonyms/acronyms** (→ jargon matching) and **provision
references** (→ authority anchoring + free silver labels). If you don't have provisions
yet, the builder can extract candidates from the definitions and the corpus.
