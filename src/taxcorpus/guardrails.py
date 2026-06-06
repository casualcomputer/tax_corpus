"""Deterministic serving guardrails — the anti-hallucination / citation / currency layer.

These run as CODE around the LLM (not as 'please remember' prompt text), which is what
makes them reliable. Targets the exact Blue J failures: fabricated citations, hallucinated
claims, and stale conclusions.
"""
from __future__ import annotations

def verify_citations(citations, retrieved):
    """Drop any citation not backed by a retrieved chunk -> fabricated-citation rate 0.
    citations: [{doc_id, paragraph_id?}]; retrieved: [chunk dicts].
    Returns (kept, dropped)."""
    exact = {(c["doc_id"], c.get("paragraph_id")) for c in retrieved}
    docs = {c["doc_id"] for c in retrieved}
    kept, dropped = [], []
    for c in citations:
        key = (c["doc_id"], c.get("paragraph_id"))
        if key in exact or (c.get("paragraph_id") is None and c["doc_id"] in docs):
            kept.append(c)
        else:
            dropped.append(c)   # not grounded in retrieved context => block it
    return kept, dropped

def currency_warning(retrieved):
    """If any supporting chunk is archived/superseded (and none current), force a caveat.
    'unknown' alone does not warn -> avoids crying wolf on undated material."""
    statuses = {c.get("status") for c in retrieved}
    if statuses & {"archived", "superseded"} and "current" not in statuses:
        sup = sorted({c["superseded_by"] for c in retrieved if c.get("superseded_by")})
        tail = f" See: {', '.join(sup)}." if sup else ""
        return ("Supporting sources are archived/superseded and may not reflect current law; "
                "verify against the current ITA, Regulations, and Income Tax Folios." + tail)
    return None

def should_abstain(top_rerank_score, threshold=0.5):
    """Prefer 'insufficient information' over a low-confidence answer."""
    return top_rerank_score is None or top_rerank_score < threshold

DISCLAIMER = ("Automated decision-support, not tax advice. CRA administrative/procedural "
              "materials are not law and may be archived; verify against the ITA, Regulations, "
              "current Income Tax Folios, and a qualified professional.")

def finalize(answer, citations, retrieved, top_score=None, threshold=0.5):
    """Apply the full guardrail chain; return a structured, safe response."""
    if should_abstain(top_score, threshold):
        return {"answer": "I don't have sufficient grounded information to answer this reliably.",
                "citations": [], "dropped_citations": citations, "warnings": [], "abstained": True,
                "disclaimer": DISCLAIMER}
    kept, dropped = verify_citations(citations, retrieved)
    warnings = [w for w in [currency_warning(retrieved)] if w]
    return {"answer": answer, "citations": kept, "dropped_citations": dropped,
            "warnings": warnings, "abstained": False, "disclaimer": DISCLAIMER}
