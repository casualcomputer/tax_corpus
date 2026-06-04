#!/usr/bin/env python3
"""
derive_training_assets.py — show how the glossary+taxonomy are CONSUMED downstream.

From data/taxonomy/taxonomy.json + data/glossary/tax_terms.jsonl, emit the concrete
assets the LLM / embedding / classification stack uses (data/derived/):

  synonyms.json            query-expansion + positive pairs (jargon <-> canonical)
  embedding_triplets.jsonl contrastive triplets (anchor, positive, STRUCTURAL hard negative)
  classification_labels.json  the multi-label topic label space (taxonomy = labels)
  provision_to_terms.json  inverse index -> silver provision-tagging key (docs/11 #4)

The point: structural hard negatives (sibling terms in a *different* node — e.g. the two
ITCs) are what make a domain retriever sharp, and they fall out of the taxonomy for free.
"""
import json, re, pathlib, itertools
ROOT = pathlib.Path(__file__).resolve().parents[1]
D = ROOT / "data" / "derived"; D.mkdir(parents=True, exist_ok=True)
nodes = json.load(open(ROOT / "data/taxonomy/taxonomy.json"))
tax = [json.loads(l) for l in open(ROOT / "data/glossary/tax_terms.jsonl")]
N = {n["id"]: n for n in nodes}
term = {t["term_id"]: t for t in tax}
def pref(t): return re.sub(r"\s*\([^)]+\)\s*$", "", t["term"]).strip()

# subject-matter membership (term -> sm nodes) for principled negatives
sm_nodes = [n for n in nodes if n["facet"] == "subject_matter" and n["glossary_terms"]]
term_sm = {}
for n in sm_nodes:
    for tid in n["glossary_terms"]:
        term_sm.setdefault(tid, set()).add(n["id"])

STOP = set("a an the of to and or in for on with by amount tax cra".split())
def words(s): return {w for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP and len(w) > 2}

# 1) synonyms / query-expansion map
syn = {}
for t in tax:
    p = pref(t)
    variants = sorted(set(t.get("synonyms", []) + ([t["term"]] if t["term"] != p else [])))
    if variants: syn[p] = variants
json.dump(syn, open(D / "synonyms.json", "w"), ensure_ascii=False, indent=2)

# 2) contrastive triplets with STRUCTURAL hard negatives (top-K, head/modifier-aware)
K = 5   # hard negatives mined per anchor; in-batch negatives supply the rest at train time

def headmods(s):
    toks = [w for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP]
    return (toks[-1] if toks else ""), set(toks[:-1])   # (head/genus, modifiers/differentia)

def relation(a, c):
    ha, ma = headmods(a); hc, mc = headmods(c)
    if ha and ha == hc and ma != mc: return "same-head/diff-modifier"   # strongest minimal pair
    if (ma & mc) and ha != hc:        return "same-modifier/diff-head"
    if (ma & mc) or ha == hc or {ha} & mc or {hc} & ma: return "partial-overlap"
    return "disjoint/easy"

def hard_negatives(t):
    # Gate on the LINGUISTIC relationship (surface-similar minimal pair), not on the taxonomy
    # node — so intra-topic contrasts (Capital gain vs Capital loss) are kept. The taxonomy
    # node/provision is logged as *confirming* metadata. Distinct glossary terms are never
    # synonyms here, so there is no false-negative risk at this (glossary) scale.
    tid = t["term_id"]; my_sm = term_sm.get(tid, set())
    my_ac = set(t.get("synonyms", [])); my_w = words(pref(t)); my_prov = set(t.get("provisions", []))
    ha, ma = headmods(pref(t)); cands = []
    for o in tax:
        if o["term_id"] == tid: continue
        rel = relation(pref(t), pref(o))
        if rel == "disjoint/easy": continue                    # not surface-similar -> easy negative, skip
        ho, mo = headmods(pref(o))
        score = (10 * len(my_ac & set(o.get("synonyms", [])))   # shared acronym (e.g. ITC) — hardest
                 + 3 * (ha == ho and bool(ha))                  # shared head/genus
                 + 2 * len(ma & mo)                             # shared modifier/differentia token
                 + 1 * len(my_w & words(pref(o))))              # any other shared word
        cands.append((score, rel, o))
    cands.sort(key=lambda x: -x[0])
    return [{"term": pref(o), "definition": o["definition"], "relation": rel,
             "cross_topic": not (term_sm.get(o["term_id"], set()) & my_sm),
             "shared_provision": bool(my_prov & set(o.get("provisions", [])))}
            for _, rel, o in cands[:K]]

triplets = []
for t in tax:
    if not t.get("definition") or t["term_id"] not in term_sm: continue
    hns = hard_negatives(t)
    if hns:
        triplets.append({"anchor": pref(t), "positive": t["definition"], "hard_negatives": hns})
with open(D / "embedding_triplets.jsonl", "w") as f:
    for r in triplets: f.write(json.dumps(r, ensure_ascii=False) + "\n")
from collections import Counter
rel_dist = Counter(h["relation"] for r in triplets for h in r["hard_negatives"])

# 3) classification label space (topic = subject_matter + taxpayer_type + process_stage)
labels = [{"id": n["id"], "label": n["prefLabel"], "facet": n["facet"], "size": len(n["glossary_terms"])}
          for n in nodes if n["facet"] in ("subject_matter", "taxpayer_type", "process_stage") and n["broader"]]
json.dump(labels, open(D / "classification_labels.json", "w"), ensure_ascii=False, indent=2)

# 4) provision -> terms inverse index (silver provision-tagging key)
prov = {}
for t in tax:
    for p in t.get("provisions", []):
        prov.setdefault(p, []).append(pref(t))
prov = {k: sorted(set(v)) for k, v in sorted(prov.items())}
json.dump(prov, open(D / "provision_to_terms.json", "w"), ensure_ascii=False, indent=2)

# samples
avg = sum(len(r["hard_negatives"]) for r in triplets) / max(len(triplets), 1)
print(f"synonyms: {len(syn)} | anchors: {len(triplets)} (avg {avg:.1f} hard-negs, K={K}) | labels: {len(labels)} | provisions: {len(prov)}")
print(f"hard-negative relation mix: {dict(rel_dist)}\n")
def show(anchor):
    r = next((x for x in triplets if x["anchor"] == anchor), None)
    if r: print(f"  {anchor}  X  " + " | ".join(f"{h['term']} [{h['relation']}]" for h in r["hard_negatives"]))
print("SAMPLE top-K structural hard negatives:")
for a in ["Input tax credit", "Capital gain", "Taxable supply", "Adjusted cost base"]: show(a)
print("\nSAMPLE provision -> terms (silver tagging):")
for k in list(prov)[:6]: print(f"  {k}: {prov[k]}")
