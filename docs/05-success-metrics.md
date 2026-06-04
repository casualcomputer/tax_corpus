# 05 — Measuring success: KPIs & acceptance gates

Two layers: **offline acceptance gates** (must pass to ship) and **online KPIs** (track
in production). Targets below are sensible defaults — **tune to your risk tolerance**;
tax errors are costly, so the safety gates are deliberately strict.

## Offline acceptance gates (block release if unmet)

| Metric | Target | Type |
|---|---|---|
| Retrieval **Recall@10** | ≥ 0.90 | quality |
| **Faithfulness / groundedness** | ≥ 0.95 | safety |
| **Ungrounded-claim (hallucination) rate** | ≤ 2% | safety |
| **Fabricated-citation rate** | **0% (hard gate)** | safety |
| **Citation precision / recall** | ≥ 0.90 / ≥ 0.85 | quality |
| **Answer correctness** (human-validated sample) | ≥ 0.85 | quality |
| **Currency-flagging recall** (currency-sensitive items) | ≥ 0.95 | safety |
| **Calibrated abstention** — correct refusal on unanswerable | ≥ 0.90 | safety |
| **Over-refusal** on answerable items | ≤ 5% | quality |
| **Authority-framing accuracy** | ≥ 0.95 | safety |
| **Human expert review** — pass rate | ≥ 0.90, **0 "materially wrong/harmful"** | safety |
| p95 latency on target hardware | within SLA (e.g., ≤ 8 s) | ops |

Two **hard gates** never trade off against capability: **fabricated-citation rate = 0**
and **0 materially-wrong/harmful** answers in expert review. A more "helpful" model that
violates either does not ship.

## Online KPIs (production)

- **Answer-accept rate** — users/experts accept without edit.
- **Expert override / edit rate** — how often a professional must correct it (trend ↓).
- **Escalation rate** — appropriately routes hard/ambiguous cases to a human.
- **User-reported error rate** + time-to-correct.
- **Time saved** per task vs. manual research (the actual business value).
- **Drift signals:** spike in low-confidence/abstentions after a CRA publication wave →
  trigger re-index + currency regression.

## How the gates map to the design

- Recall@k / citation-hit-rate ← hybrid retrieval + reranker + chunking quality (`03`).
- Faithfulness / ungrounded-rate ← citation-constrained prompt + cite-verify guardrail (`02`).
- Fabricated-citation = 0 ← deterministic post-gen citation verification (`02`).
- Currency-flagging ← `status`/`issue_date` metadata + currency guardrail (`02`,`03`).
- Calibrated abstention ← reranker score threshold + SFT abstention examples (`01`,`02`).

## Reporting

- A one-page **scorecard** per release: every gate, green/red, delta vs. previous.
- A **model/data card**: corpus snapshot date, source `status` distribution, known gaps
  (missing ITA/Folios/case law), eval-set version, judge↔human κ.
- The standing disclaimer travels with every answer **and** every report: this is
  decision-support, **not** tax advice; verify against the ITA, current Income Tax
  Folios, and a qualified professional.
