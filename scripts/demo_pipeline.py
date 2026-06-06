#!/usr/bin/env python3
"""End-to-end proof of the engine on a SYNTHETIC Interpretation Bulletin (no network).

Shows: structure-aware parse -> paragraph-anchored chunks with provisions + doc-level
status; the cite-verify guardrail dropping a fabricated citation; the currency caveat
firing on an archived source; abstention on low confidence; and an eval scorecard.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from taxcorpus import ingest, guardrails, eval_harness

HTML = """
<html><head><title>IT-518R</title></head><body>
<nav>breadcrumbs / menu junk</nav>
<h1>IT-518R Food, Beverages and Entertainment Expenses</h1>
<p>This bulletin is archived and has been superseded by Income Tax Folio S3-F6-C1.</p>
<h2>Discussion and Interpretation</h2>
<p>1. Under section 67.1, the amount deductible for food, beverages and entertainment is
   generally limited to 50% of the lesser of the actual cost and a reasonable amount.</p>
<p>2. Subsection 20(1)(c) and paragraph 8(1)(h.1) are addressed separately; see also IT-470R.</p>
<p>3. For GST/HST, ETA 123(1) defines "consideration".</p>
<footer>footer junk</footer></body></html>
"""

blocks = ingest.html_to_blocks(HTML)
chunks = ingest.chunk_blocks(blocks, doc_id="IT-518R", source_type="interpretation_bulletin",
                             source_url="https://example/IT-518R", retrieved_at="2026-06-06T00:00:00Z",
                             default_authority="cra_administrative_position")

print("=== chunks (paragraph anchors + provisions + doc-level status) ===")
for c in chunks:
    print(f"  {c['chunk_id']:12} para={c['paragraph_id']} status={c['status']:10} "
          f"prov={c['ita_sections']}  | {c['text'][:55]}...")

bypid = {c["paragraph_id"]: c for c in chunks}
assert [c["paragraph_id"] for c in chunks if c["paragraph_id"]] == ["1", "2", "3"], "paragraph anchors lost"
assert "67.1" in bypid["1"]["ita_sections"] and "20(1)(c)" in bypid["2"]["ita_sections"]
assert all(c["status"] == "superseded" for c in chunks), "doc-level archived/superseded not propagated"
assert bypid["1"]["superseded_by"] and "folio" in bypid["1"]["superseded_by"].lower()

# --- serving guardrails: retrieve paras 1 & 3; model cites one REAL + one FABRICATED para ---
retrieved = [c for c in chunks if c["paragraph_id"] in ("1", "3")]
answer = "Meals and entertainment are generally 50% deductible under section 67.1."
citations = [{"doc_id": "IT-518R", "paragraph_id": "1"},     # grounded
             {"doc_id": "IT-518R", "paragraph_id": "9"}]     # fabricated (para 9 not retrieved)
resp = guardrails.finalize(answer, citations, retrieved, top_score=0.82)

print("\n=== guardrailed response ===")
print("  kept citations :", resp["citations"])
print("  DROPPED (halluc):", resp["dropped_citations"])
print("  warnings        :", resp["warnings"])
print("  abstained       :", resp["abstained"])
assert resp["citations"] == [{"doc_id": "IT-518R", "paragraph_id": "1"}], "grounded cite missing"
assert resp["dropped_citations"] == [{"doc_id": "IT-518R", "paragraph_id": "9"}], "fabricated cite not dropped"
assert resp["warnings"], "currency warning should fire (archived/superseded source)"

low = guardrails.finalize(answer, citations, retrieved, top_score=0.30)
assert low["abstained"] and low["citations"] == [], "should abstain on low confidence"
print("  low-confidence ->", low["answer"])

# --- eval harness smoke test ---
items = [
    {"id": "q1", "question": "What portion of meals is deductible?", "item_type": "gold",
     "answer_type": "interpretive", "validated": True, "currency_sensitive": True,
     "relevant_chunk_ids": ["IT-518R#1"], "required_citations": [{"doc_id": "IT-518R", "paragraph_id": "1"}]},
    {"id": "r1", "question": "How is GST calculated in Ontario?", "item_type": "red_team",
     "answer_type": "out_of_scope", "validated": True, "currency_sensitive": False},
]
def retrieve_fn(q):
    return [c for c in chunks if c["paragraph_id"] == "1"] if "meals" in q.lower() else []
def respond_fn(q, cs):
    if not cs:  # out of scope -> abstain
        return guardrails.finalize("", [], [], top_score=0.0)
    return guardrails.finalize("Generally 50% under section 67.1.",
                               [{"doc_id": "IT-518R", "paragraph_id": "1"}], cs, top_score=0.8)
report = eval_harness.evaluate(items, retrieve_fn, respond_fn, k=10)
print("\n=== eval scorecard ===")
for k, v in report["scorecard"].items():
    print(f"  {k}: {v}")
assert report["scorecard"]["fabricated_cites"] == 0
assert report["scorecard"]["abstain_ok"] == 1.0 and report["scorecard"]["currency_ok"] == 1.0
print("\nALL ASSERTIONS PASSED ✓")
