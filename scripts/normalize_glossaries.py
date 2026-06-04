#!/usr/bin/env python3
"""
normalize_glossaries.py — CRA glossary .xlsx -> normalized JSONL (schemas/glossary_term.schema.json).

  inputs : data/glossary/source/CRA_Tax_Terminology_Glossary.xlsx  (sheet 'Glossary')
           data/glossary/source/CRA_Program_Acronym_Glossary.xlsx  (sheet 'Acronyms')
  output : data/glossary/tax_terms.jsonl   (term_id = slug(term))
           data/glossary/acronyms.jsonl    (term_id = slug(initialism); collisions suffixed)

Tax terms keep their source `Domain` and `Legal/technical flag`. Acronyms are keyed by the
initialism (so 'ITA' and the shorthand 'Act' for the same full form stay distinct, and
overloaded initialisms like 'AD' are suffixed -2). Requires: openpyxl.
"""
import openpyxl, json, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "glossary" / "source"
OUT = ROOT / "data" / "glossary"

def slug(s): return re.sub(r"[^a-z0-9]+", "-", (s or "").strip().lower()).strip("-")[:60]

def rows(fn, sheet):
    wb = openpyxl.load_workbook(SRC / fn, read_only=True, data_only=True)
    rs = [r for r in wb[sheet].iter_rows(values_only=True)]; wb.close()
    hi = next(i for i, r in enumerate(rs)
              if r and any(c in ("Term", "Acronym / initialism") for c in r if isinstance(c, str)))
    hdr = [(c or "").strip() for c in rs[hi]]
    out = []
    for r in rs[hi + 1:]:
        if not r or all(c is None for c in r): continue
        d = {hdr[i]: (str(r[i]).strip() if i < len(r) and r[i] is not None else None)
             for i in range(len(hdr)) if hdr[i]}
        if d.get("Term") or d.get("Acronym / initialism"): out.append(d)
    return out

def uniq(base, seen):
    i, k = 1, base
    while k in seen: i += 1; k = f"{base}-{i}"
    seen.add(k); return k

# tax terms
tax, seen = [], set()
for d in rows("CRA_Tax_Terminology_Glossary.xlsx", "Glossary"):
    tax.append({"term_id": uniq(slug(d.get("Term")), seen), "term": d.get("Term"),
                "definition": d.get("Plain-language definition"), "synonyms": [], "see_also": [],
                "provisions": [], "domain": d.get("Domain"), "category": None,
                "legal_flag": d.get("Legal / technical flag"), "notes": None,
                "source": d.get("Source family"), "source_url": d.get("Source URL"), "language": "en"})

# acronyms (keyed by initialism)
acr, seen = [], set()
for d in rows("CRA_Program_Acronym_Glossary.xlsx", "Acronyms"):
    a = d.get("Acronym / initialism"); full = d.get("Full form")
    acr.append({"term_id": uniq(slug(a or full), seen), "term": full or a, "definition": full,
                "synonyms": [a] if a else [], "see_also": [], "provisions": [],
                "domain": d.get("Source family"), "category": d.get("Category"), "legal_flag": None,
                "notes": d.get("Notes"), "source": d.get("Source family"),
                "source_url": d.get("Source URL"), "language": "en"})

for name, recs in [("tax_terms.jsonl", tax), ("acronyms.jsonl", acr)]:
    with open(OUT / name, "w", encoding="utf-8") as f:
        for r in recs: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"wrote {len(tax)} tax terms, {len(acr)} acronyms")
