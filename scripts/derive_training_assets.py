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

# 2) contrastive triplets with STRUCTURAL hard negatives
def hard_negative(t):
    tid = t["term_id"]; my_sm = term_sm.get(tid, set()); my_ac = set(t.get("synonyms", [])); my_w = words(pref(t))
    best, bs = None, -1
    for o in tax:
        oid = o["term_id"]
        if oid == tid or (term_sm.get(oid, set()) & my_sm):   # must be a DIFFERENT subject node
            continue
        s = 10 * len(my_ac & set(o.get("synonyms", []))) + len(my_w & words(pref(o)))  # shared acronym >> shared word
        if s > bs: best, bs = o, s
    return best, bs
triplets = []
for t in tax:
    if not t.get("definition") or t["term_id"] not in term_sm: continue
    hn, score = hard_negative(t)
    if not hn: continue
    triplets.append({"anchor": pref(t), "positive": t["definition"],
                     "hard_negative": pref(hn), "hard_negative_definition": hn["definition"],
                     "shared_signal": ("acronym" if score >= 10 else "lexical" if score > 0 else "sibling-facet")})
with open(D / "embedding_triplets.jsonl", "w") as f:
    for r in triplets: f.write(json.dumps(r, ensure_ascii=False) + "\n")

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
print(f"synonyms: {len(syn)} | triplets: {len(triplets)} | labels: {len(labels)} | provisions: {len(prov)}\n")
print("SAMPLE structural hard negatives (anchor  X  hard-negative  [signal]):")
for r in [x for x in triplets if x["shared_signal"] == "acronym"][:3] + triplets[:2]:
    print(f"  {r['anchor']!r}  X  {r['hard_negative']!r}  [{r['shared_signal']}]")
print("\nSAMPLE provision -> terms (silver tagging):")
for k in list(prov)[:6]: print(f"  {k}: {prov[k]}")
