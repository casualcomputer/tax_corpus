# 06 — Tax-domain notes (read before building)

What separates a credible tax system from a plausible-sounding one is correct handling of
**authority**, **currency**, and **scope**. These are domain facts, not ML choices.

## Authority hierarchy (most → least binding)

1. **Income Tax Act (ITA) + Income Tax Regulations** — the law.
2. **Case law** — Tax Court of Canada, Federal Court of Appeal, Supreme Court of Canada.
3. **Income Tax Folios** — CRA's *current* consolidated administrative positions (the
   modern replacement for ITs).
4. **Interpretation Bulletins (ITs)** — CRA's older administrative positions; **largely
   archived/superseded**.
5. **Technical interpretations & advance income tax rulings** — CRA views, often
   taxpayer/fact-specific (rulings bind CRA only for the specific taxpayer/facts).
6. **Income Tax Audit Manual** — CRA **internal procedure** for auditors.
7. Guides, pamphlets, web pages — general info.

Key point a model must respect: **ITs, Folios, and the Audit Manual are CRA's views, not
law.** They are persuasive but **do not bind the courts**, and CRA can change position.
Never present any of them as binding statute.

## Interpretation Bulletins: currency is a first-class concern

- CRA began **replacing ITs with Income Tax Folios in 2013**; many ITs are **archived**
  and some positions are **outdated** (post-IT legislative/jurisprudential change).
- Therefore: track `status` (`current`/`archived`/`superseded`) and `superseded_by`
  (the Folio), and **always surface issue date + status**. Serving an archived IT as
  current policy is a top-tier failure (see the hard gates in `05-success-metrics.md`).

## The Audit Manual: what it is / isn't

- Internal **procedural** guidance: case selection, risk assessment, audit techniques
  (e.g., **net-worth / indirect verification** methods for inadequate books, deposit
  analysis, ratio/markup analysis), documentation, taxpayer rights, referrals.
- Released publicly (often via ATIP) and may contain **redactions**; reflects CRA's
  **operational stance at time of release** — also date- and version-sensitive.
- Great for teaching a model *how CRA reasons about compliance/risk*; not a source of
  statutory authority.

## Scope boundaries (what these two sources do NOT cover)

- **GST/HST**, **payroll/source deductions**, **excise**, **customs** — different regimes.
- **Provincial tax** — and note **Quebec** administers its own income tax via **Revenu
  Québec** (the ITA/CRA corpus does not speak for it).
- **US / foreign tax**, treaties (beyond what an IT happens to touch).
- Out-of-scope questions should trigger **abstention/clarification**, not a guess.

## To become a *general* Canadian income-tax assistant, add (priority order)

1. **ITA + Regulations** (the law itself).
2. **Income Tax Folios** (supersede the ITs).
3. CRA **technical interpretations / advance rulings**.
4. **Tax Court / FCA / SCC** case law.
5. Annual **budget & enacted legislative** changes (currency feed).

## Legal / usage & privacy

- CRA materials are **Crown copyright**. Non-commercial reproduction is generally
  permitted **with source attribution** and without representing it as an official
  version; **commercial use typically requires permission**. Confirm terms for your use.
- Keep raw `source_url` + `retrieved_at` for attribution and audit.
- **Privacy:** a local deployment is the right choice for taxpayer data; still, don't log
  prompts/answers containing taxpayer PII to anything off-box, and segregate any
  taxpayer-specific data from the public corpus.

## The standing disclaimer (ship it with every answer)

> This is automated **decision-support**, not tax advice. Positions are drawn from CRA
> administrative/procedural materials that may be **archived or superseded** and are **not
> law**. Verify against the current Income Tax Act, Regulations, Income Tax Folios, and a
> qualified tax professional before relying on any conclusion.
