#!/usr/bin/env python3
"""
build_taxonomy.py — induce the tax topic taxonomy from the two CRA glossaries.

Implements docs/12-glossary-to-taxonomy.md for THIS data:
  inputs : data/glossary/tax_terms.jsonl, data/glossary/acronyms.jsonl
  output : data/taxonomy/taxonomy.json        (SKOS-aligned nodes; schemas/taxonomy_node.schema.json)
           data/taxonomy/coverage_report.md   (coverage / balance / SME-review queue)
  side   : enriches tax_terms.jsonl with altLabels (synonyms) + model-proposed provisions

Method: skeleton (ITA-anchored, faceted) -> reconcile the source `Domain` column ->
curated poly-hierarchy + provision overrides -> acronym grouping -> coverage report.
ALL placements/provisions are method='llm'/'skeleton' and validated=false: they are
SME-review candidates, not authority. GST/HST provisions are cited to the Excise Tax
Act (ETA), not the Income Tax Act.
"""
import json, re, os, pathlib
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
G = ROOT / "data" / "glossary"
T = ROOT / "data" / "taxonomy"; T.mkdir(parents=True, exist_ok=True)

def load(p): return [json.loads(l) for l in open(p, encoding="utf-8")]
tax = load(G / "tax_terms.jsonl")
acro = load(G / "acronyms.jsonl")

# ---------------- skeleton (top-down, ITA/ETA-anchored + facets) ----------------
def node(id, label, facet, broader=None, definition=None):
    return {"id": id, "prefLabel": label, "altLabel": [], "definition": definition,
            "facet": facet, "broader": broader, "broader_all": [broader] if broader else [],
            "narrower": [], "related": [], "mapped_provisions": [], "glossary_terms": [],
            "method": "skeleton", "validated": False}

N = {}
def add(*args): n = node(*args); N[n["id"]] = n; return n["id"]

# subject_matter (anchored on ITA Part I / Division B subdivisions + GST/HST + admin)
add("sm-root", "Tax subject matter", "subject_matter")
for i, l in [
    ("sm-income", "Income & its computation"),
    ("sm-capital", "Capital gains & property"),
    ("sm-gst-hst", "GST/HST"),
    ("sm-registered-plans", "Registered & savings plans"),
    ("sm-charities", "Charities & donations"),
    ("sm-incentives", "Tax incentives & shelters"),
    ("sm-business-accounting", "Business & accounting concepts"),
    ("sm-credits-deductions", "Credits, deductions & benefits"),
    ("sm-structural", "Structural & general legal concepts"),
]: add(i, l, "subject_matter", "sm-root")

# process_stage (compliance lifecycle; seeded by Audit Manual + admin terms)
add("ps-root", "Compliance lifecycle", "process_stage")
for i, l in [("ps-filing", "Filing & registration"), ("ps-assessment", "Assessment & reassessment"),
             ("ps-payment-collection", "Payment, refund & collection"), ("ps-audit", "Audit & examination"),
             ("ps-appeals", "Objections & appeals"), ("ps-sred-review", "SR&ED review")]:
    add(i, l, "process_stage", "ps-root")

# taxpayer_type
add("tt-root", "Taxpayer / entity type", "taxpayer_type")
for i, l in [("tt-individual", "Individual"), ("tt-business", "Unincorporated business"),
             ("tt-corporation", "Corporation"), ("tt-partnership", "Partnership"),
             ("tt-charity", "Charity / qualified donee"), ("tt-registrant", "GST/HST registrant"),
             ("tt-plan-holder", "Registered-plan holder")]:
    add(i, l, "taxpayer_type", "tt-root")

# authority_tier
add("auth-root", "Authority", "authority_tier")
for i, l in [("auth-legislation", "Legislation (ITA / ETA / Regulations)"),
             ("auth-accounting-standard", "Accounting / audit standards (IFRS/GAAP/ASPE)"),
             ("auth-cra-interpretation", "CRA administrative positions (IT / Folio)")]:
    add(i, l, "authority_tier", "auth-root")

# program_entity (from the acronym glossary — CRA org/system/role/document jargon)
add("pe-root", "CRA program entities", "program_entity")
for i, l in [("pe-org", "Organizational units"), ("pe-role", "Roles & specialists"),
             ("pe-system", "Systems & tools"), ("pe-document", "Manuals, reports & forms"),
             ("pe-audit-concept", "Audit / review concepts"), ("pe-sred", "SR&ED program concepts"),
             ("pe-external", "External bodies & oversight"), ("pe-other", "Other program acronyms (triage)")]:
    add(i, l, "program_entity", "pe-root")

# ---------------- domain -> default subject_matter ----------------
DOMAIN = {
    "Business / CRA admin": "sm-business-accounting", "Business": "sm-business-accounting",
    "Capital gains": "sm-capital", "Individual tax": "sm-credits-deductions",
    "Individual / benefits": "sm-credits-deductions", "Business / income tax": "sm-income",
    "Business / property": "sm-capital", "GST/HST": "sm-gst-hst", "Business / T2": "sm-business-accounting",
    "Individual / business tax": "sm-credits-deductions", "RESP": "sm-registered-plans",
    "Registered plans": "sm-registered-plans", "FHSA": "sm-registered-plans",
    "Flow-through shares": "sm-incentives", "Charities / donations": "sm-charities",
    "Tax shelters": "sm-incentives", "Benefits": "sm-credits-deductions", "RRSP / housing": "sm-registered-plans",
    "SR&ED / business tax": "sm-incentives", "RRSP / education": "sm-registered-plans",
    "CRA admin": None, "Payroll": None, "Tax shelters / technical": "sm-incentives",
    "Legal / income tax": "sm-structural", "Charities": "sm-charities", "Pensions": "sm-registered-plans",
    "SR&ED": "sm-incentives",
}

# ---------------- curated overrides (poly-hierarchy + facets + provisions) ----------------
# sm/tt/ps = node ids; prov = model-proposed provisions (SME to verify). ETA = Excise Tax Act.
OV = {
 "Adjusted cost base (ACB)": {"prov": ["54"]},
 "Capital cost allowance (CCA)": {"sm": ["sm-capital", "sm-income"], "prov": ["20(1)(a)", "Reg 1100"]},
 "Capital gain": {"prov": ["39(1)(a)", "40"]},
 "Capital loss": {"prov": ["39(1)(b)", "40"]},
 "Capital property": {"prov": ["54"]},
 "Taxable capital gain": {"prov": ["38(a)"]},
 "Disposition": {"prov": ["248(1)"]},
 "Proceeds of disposition": {"prov": ["54"]},
 "Principal residence": {"prov": ["54", "40(2)(b)"]},
 "Superficial loss": {"prov": ["54", "40(2)(g)"]},
 "Depreciable property": {"sm": ["sm-capital", "sm-income"], "prov": ["13(21)", "Reg 1100"]},
 "Employment income": {"sm": ["sm-income"], "tt": ["tt-individual"], "prov": ["5", "6"]},
 "Business income": {"sm": ["sm-income", "sm-business-accounting"], "prov": ["9"]},
 "Net income": {"sm": ["sm-income"], "prov": ["3"]},
 "Taxable income": {"sm": ["sm-income"], "prov": ["2(2)"]},
 "Inventory": {"sm": ["sm-business-accounting"], "prov": ["10", "248(1)"]},
 "Fiscal period": {"sm": ["sm-business-accounting"], "prov": ["249.1"]},
 "Corporation": {"sm": ["sm-business-accounting"], "tt": ["tt-corporation"], "prov": ["248(1)"]},
 "Partnership": {"sm": ["sm-business-accounting"], "tt": ["tt-partnership"], "prov": ["96", "102"]},
 "Property": {"sm": ["sm-structural"], "prov": ["248(1)"]},
 "Deduction": {"sm": ["sm-credits-deductions"]},
 "Tax deduction": {"sm": ["sm-credits-deductions"]},
 "Tax credit": {"sm": ["sm-credits-deductions"]},
 "Benefit": {"sm": ["sm-credits-deductions"]},
 "Eligible child": {"sm": ["sm-credits-deductions"], "tt": ["tt-individual"]},
 "Common-law partner": {"sm": ["sm-structural"], "tt": ["tt-individual"], "prov": ["248(1)"]},
 "Spouse or common-law partner amount": {"sm": ["sm-credits-deductions"], "tt": ["tt-individual"], "prov": ["118(1)"]},
 "GST/HST credit": {"sm": ["sm-credits-deductions", "sm-gst-hst"], "tt": ["tt-individual"], "prov": ["122.5"]},
 "Balance owing": {"sm": [], "ps": ["ps-payment-collection"]},
 "Refund": {"sm": [], "ps": ["ps-payment-collection"], "prov": ["164"]},
 "Remittance": {"sm": [], "ps": ["ps-payment-collection"]},
 "Payroll remittance": {"sm": ["sm-business-accounting"], "ps": ["ps-payment-collection"], "prov": ["153"]},
 "Notice of assessment (NOA)": {"sm": [], "ps": ["ps-assessment"], "prov": ["152"]},
 "Reassessment": {"sm": [], "ps": ["ps-assessment"], "prov": ["152(4)"]},
 "Return": {"sm": [], "ps": ["ps-filing"], "prov": ["150"]},
 "Income tax return": {"sm": [], "ps": ["ps-filing"], "tt": ["tt-individual"], "prov": ["150"]},
 # GST/HST -> Excise Tax Act
 "Supply": {"prov": ["ETA 123(1)"]},
 "Taxable supply": {"prov": ["ETA 123(1)"]},
 "Exempt supply": {"prov": ["ETA 123(1)", "ETA Sch V"]},
 "Zero-rated supply": {"prov": ["ETA 123(1)", "ETA Sch VI"]},
 "Commercial activity": {"prov": ["ETA 123(1)"]},
 "Consideration": {"prov": ["ETA 123(1)"]},
 "Input tax credit (ITC)": {"tt": ["tt-registrant"], "prov": ["ETA 169"]},
 "Net tax": {"prov": ["ETA 225", "ETA 228"]},
 "Place of supply": {"prov": ["ETA 144.1"]},
 "Participating province": {"prov": ["ETA 123(1)"]},
 "GST/HST registrant": {"tt": ["tt-registrant"], "prov": ["ETA 240", "ETA 123(1)"]},
 "Small supplier": {"tt": ["tt-registrant"], "prov": ["ETA 148"]},
 # charities
 "Registered charity": {"tt": ["tt-charity"], "prov": ["248(1)", "149.1"]},
 "Qualified donee": {"prov": ["149.1(1)"]},
 "Gift": {"prov": ["118.1"]},
 "Official donation receipt": {"prov": ["Reg 3501"]},
 # incentives / shelters
 "Tax shelter": {"prov": ["237.1"]},
 "Tax shelter identification number": {"prov": ["237.1"]},
 "Gifting arrangement": {"sm": ["sm-incentives", "sm-charities"], "prov": ["237.1"]},
 "Promoter": {"prov": ["237.1(1)"]},
 "Flow-through share (FTS)": {"prov": ["66(15)"]},
 "Investment tax credit (ITC)": {"prov": ["127(5)", "127(9)"]},
 "Scientific research and experimental development (SR&ED)": {"ps": ["ps-sred-review"], "prov": ["37", "248(1)"]},
 # registered plans
 "Registered education savings plan (RESP)": {"tt": ["tt-plan-holder"], "prov": ["146.1"]},
 "Educational assistance payment (EAP)": {"prov": ["146.1(1)"]},
 "Subscriber": {"tt": ["tt-individual"], "prov": ["146.1(1)"]},
 "First Home Savings Account (FHSA)": {"tt": ["tt-plan-holder"], "prov": ["146.6"]},
 "FHSA participation room": {"prov": ["146.6(1)"]},
 "Home Buyers’ Plan (HBP)": {"tt": ["tt-individual"], "prov": ["146.01"]},
 "Lifelong Learning Plan (LLP)": {"tt": ["tt-individual"], "prov": ["146.02"]},
 "Registered retirement savings plan (RRSP)": {"tt": ["tt-plan-holder"], "prov": ["146"]},
 "Registered retirement income fund (RRIF)": {"tt": ["tt-plan-holder"], "prov": ["146.3"]},
 "Registered pension plan (RPP)": {"tt": ["tt-plan-holder"], "prov": ["147.1"]},
 "Tax-Free Savings Account (TFSA)": {"tt": ["tt-plan-holder"], "prov": ["146.2"]},
}

def split_acronym(term):
    m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", term)
    return (m.group(1).strip(), [m.group(2).strip()]) if m else (term, [])

# ---------------- assign tax terms ----------------
unplaced = []
for t in tax:
    name = t["term"]; ov = OV.get(name, {})
    pref, alt = split_acronym(name)
    t["synonyms"] = sorted(set(t.get("synonyms", []) + alt))
    if ov.get("prov"):
        t["provisions"] = ov["prov"]
    sm = ov.get("sm")
    if sm is None:
        d = DOMAIN.get(t.get("domain"))
        sm = [d] if d else []
    targets = list(sm) + ov.get("tt", []) + ov.get("ps", [])
    if not targets:
        unplaced.append(name)
    for nid in targets:
        N[nid]["glossary_terms"].append(t["term_id"])
        for p in t["provisions"]:
            if p not in N[nid]["mapped_provisions"]:
                N[nid]["mapped_provisions"].append(p)
    # carry acronym altLabel up to the first subject node for matching
    for nid in (sm[:1] or targets[:1]):
        for a in alt:
            if a not in N[nid]["altLabel"]:
                N[nid]["altLabel"].append(a)

# ---------------- group acronyms ----------------
CAT = {
 "Agency": "pe-org", "Branch": "pe-org", "Directorate": "pe-org", "Division": "pe-org",
 "Office": "pe-org", "Organization": "pe-org", "Centre of expertise": "pe-org",
 "Role": "pe-role", "Specialist role": "pe-role", "Specialist service": "pe-role", "Party": "pe-role",
 "System": "pe-system", "Tool": "pe-system", "Risk tool": "pe-system",
 "Software / audit tool": "pe-system", "System/report": "pe-system", "Access control": "pe-system",
 "Manual": "pe-document", "Report": "pe-document", "Publication type": "pe-document",
 "CRA publication": "pe-document", "Document type": "pe-document", "Document structure": "pe-document",
 "Form / return": "pe-document", "Slip": "pe-document",
 "Legislation": "auth-legislation", "Legislation shorthand": "auth-legislation",
 "Accounting standard": "auth-accounting-standard", "Audit standard": "auth-accounting-standard",
 "Financial reporting": "auth-accounting-standard",
 "Audit approach": "ps-audit", "Audit quality": "ps-audit", "Audit measure": "ps-audit",
 "Audit / review": "ps-audit", "Review outcome": "ps-audit", "Review / compliance": "ps-audit",
 "Review / oversight": "ps-audit", "Quality control": "ps-audit", "Internal audit": "ps-audit",
 "Review process": "ps-audit", "Control concept": "ps-audit", "Program / audit": "ps-audit",
 "Appeals / dispute": "ps-appeals",
 "SR&ED review concept": "pe-sred", "SR&ED review role/function": "pe-sred",
 "SR&ED eligibility concept": "pe-sred", "SR&ED production concept": "pe-sred",
 "SR&ED tax concept": "pe-sred", "Tax / SR&ED": "pe-sred",
 "External association": "pe-external", "External professional body": "pe-external",
 "External oversight body": "pe-external", "External government entity": "pe-external",
 "External agency": "pe-external", "Governance committee": "pe-external",
 "Corporation type": "tt-corporation",
}
term_slug = {t["term_id"]: t for t in tax}
pref_index = {}
for t in tax:
    p, _ = split_acronym(t["term"]); pref_index[re.sub(r'[^a-z0-9]+','-',p.lower()).strip('-')] = t

merged_as_altlabel = 0
for a in acro:
    full = (a.get("term") or "").strip(); ac = (a["synonyms"][0] if a["synonyms"] else "")
    key = re.sub(r'[^a-z0-9]+','-', full.lower()).strip('-')
    if key in pref_index:  # acronym expands a known tax term -> altLabel, not a new node
        t = pref_index[key]
        if ac and ac not in t["synonyms"]:
            t["synonyms"].append(ac); merged_as_altlabel += 1
        continue
    nid = CAT.get(a.get("category"), "pe-other")
    N[nid]["glossary_terms"].append(a["term_id"])
    if ac and ac not in N[nid]["altLabel"]:
        N[nid]["altLabel"].append(ac)

# rebuild narrower from broader; drop empty leaf skeleton nodes for cleanliness
for n in N.values():
    if n["broader"]:
        N[n["broader"]]["narrower"].append(n["id"])
nodes = [n for n in N.values() if n["glossary_terms"] or n["narrower"] or n["broader"] is None]

# ---------------- write outputs ----------------
with open(G / "tax_terms.jsonl", "w", encoding="utf-8") as f:
    for t in tax: f.write(json.dumps(t, ensure_ascii=False) + "\n")
with open(T / "taxonomy.json", "w", encoding="utf-8") as f:
    json.dump(nodes, f, ensure_ascii=False, indent=2)

# coverage / balance / SME queue
by_facet = Counter(n["facet"] for n in nodes)
placed = sum(len(n["glossary_terms"]) for n in N.values() if n["facet"] == "subject_matter")
sizes = sorted(((len(n["glossary_terms"]), n["id"]) for n in nodes if n["glossary_terms"]), reverse=True)
prov_terms = sum(1 for t in tax if t["provisions"])
lines = ["# Taxonomy coverage report", "",
    f"- Tax terms: **{len(tax)}**  |  Acronyms: **{len(acro)}** (merged as altLabel: {merged_as_altlabel}, grouped: {len(acro)-merged_as_altlabel})",
    f"- Nodes: **{len(nodes)}** across facets: " + ", ".join(f"{k} {v}" for k,v in by_facet.items()),
    f"- Tax terms with a subject-matter placement: **{len(tax)-len(unplaced)}/{len(tax)}**",
    f"- Tax terms with a model-proposed provision (SME to verify): **{prov_terms}/{len(tax)}**",
    "", "## Largest nodes (watch for over-broad buckets)"]
for c, i in sizes[:12]: lines.append(f"- `{i}` ({N[i]['prefLabel']}): {c}")
lines += ["", "## SME-review queue", "",
    "- **Unplaced tax terms (need a subject node):** " + (", ".join(unplaced) or "none"),
    "- **All placements & provisions are `validated:false`** (method=llm/skeleton) — confirm before use.",
    "- **GST/HST provisions cite the Excise Tax Act (ETA)**, not the ITA — verify.",
    "- **`pe-other`** holds uncategorized program acronyms — triage into a facet.",
    "- Overloaded initialisms (e.g., ITC = Input tax credit vs Investment tax credit; AD) kept as distinct terms."]
open(T / "coverage_report.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")

# human-readable tree (for SME browsing)
label = {t["term_id"]: split_acronym(t["term"])[0] for t in tax}
label.update({a["term_id"]: (a["synonyms"][0] if a["synonyms"] else a["term"]) for a in acro})
roots = [n for n in nodes if n["broader"] is None]
tree = ["# Taxonomy tree (term counts; sample members)", ""]
def walk(nid, depth):
    n = N[nid]; terms = n["glossary_terms"]
    head = f"{'  '*depth}- **{n['prefLabel']}** ({len(terms)})"
    if terms:
        sample = ", ".join(label.get(x, x) for x in terms[:6]) + (" …" if len(terms) > 6 else "")
        head += f" — {sample}"
    tree.append(head)
    for c in n["narrower"]: walk(c, depth + 1)
for r in sorted(roots, key=lambda x: x["facet"]):
    walk(r["id"], 0)
open(T / "taxonomy_tree.md", "w", encoding="utf-8").write("\n".join(tree) + "\n")

print("\n".join(lines))