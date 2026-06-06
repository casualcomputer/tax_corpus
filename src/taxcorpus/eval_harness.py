"""Minimal, dependency-free eval harness wired to schemas/eval_item.schema.json.

Computes the gates from docs/05 that don't need a model (retrieval recall, citation
precision, currency-flagging, abstention). Faithfulness is pluggable: pass an
entailment/LLM scorer, or use the lexical-overlap fallback for an offline smoke test.
"""
from __future__ import annotations
import json

def load_items(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]

def recall_at_k(relevant_ids, ranked_ids, k=10):
    if not relevant_ids: return None
    top = set(ranked_ids[:k])
    return len(top & set(relevant_ids)) / len(set(relevant_ids))

def citation_metrics(pred, required):
    """pred/required: lists of {doc_id, paragraph_id?}. Returns (precision, recall)."""
    def norm(cs): return {(c["doc_id"], c.get("paragraph_id")) for c in cs}
    p, r = norm(pred), norm(required)
    if not p and not r: return (1.0, 1.0)
    prec = len(p & r) / len(p) if p else 0.0
    rec = len(p & r) / len(r) if r else 1.0
    return (prec, rec)

def lexical_faithfulness(answer, retrieved_texts):
    """Fallback only: fraction of answer content-words present in the retrieved context."""
    import re
    aw = {w for w in re.findall(r"[a-z]{4,}", answer.lower())}
    if not aw: return 1.0
    ctx = " ".join(retrieved_texts).lower()
    return sum(1 for w in aw if w in ctx) / len(aw)

def evaluate(items, retrieve_fn, respond_fn, k=10, faithfulness_fn=None):
    """retrieve_fn(question)->[chunk dicts]; respond_fn(question, chunks)->guardrails.finalize() dict."""
    faithfulness_fn = faithfulness_fn or (lambda a, ts: lexical_faithfulness(a, ts))
    rows, agg = [], {"recall@k": [], "cite_precision": [], "faithfulness": [],
                     "currency_ok": [], "abstain_ok": [], "fabricated_cites": 0}
    for it in items:
        chunks = retrieve_fn(it["question"])
        out = respond_fn(it["question"], chunks)
        agg["fabricated_cites"] += len(out.get("dropped_citations", []))
        oos = it.get("answer_type") == "out_of_scope" or it.get("item_type") == "red_team"
        agg["abstain_ok"].append(float(out["abstained"] == bool(oos)) if oos else None)
        if not oos:
            rk = recall_at_k(it.get("relevant_chunk_ids", []), [c["chunk_id"] for c in chunks], k)
            if rk is not None: agg["recall@k"].append(rk)
            prec, _ = citation_metrics(out["citations"], it.get("required_citations", []))
            agg["cite_precision"].append(prec)
            agg["faithfulness"].append(faithfulness_fn(out["answer"], [c["text"] for c in chunks]))
            if it.get("currency_sensitive"):
                agg["currency_ok"].append(float(bool(out["warnings"])))
        rows.append({"id": it["id"], "abstained": out["abstained"],
                     "n_citations": len(out["citations"]), "n_dropped": len(out.get("dropped_citations", []))})
    def mean(xs): xs = [x for x in xs if x is not None]; return round(sum(xs) / len(xs), 3) if xs else None
    scorecard = {k2: (mean(v) if isinstance(v, list) else v) for k2, v in agg.items()}
    return {"scorecard": scorecard, "rows": rows}
