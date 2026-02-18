# Manual Review Workflow (Wireframe)

## Objective
Flag ambiguous or low‑confidence transactions, route them for human approval, and capture decisions for rule improvement.

---

## Entry Criteria
A transaction enters the review queue if:
- `confidence < 0.85`, or
- rule specifies `requires_review = true`, or
- no match found.

---

## Review Steps
1. **Queue**: items appear in `pending` state.
2. **Inspect**: reviewer sees raw transaction + proposed ledger + reason.
3. **Decide**: approve, reject, or defer.
4. **Annotate**: add notes or corrected category.
5. **Learn**: optional rule suggestion generated.

---

## Review UI (Minimal)
- Table with filters by date, vendor, job, phase.
- Confidence score and reason.
- One‑click approve/reject.
- Inline category override.
- Notes field.

---

## Outputs
- `review_log.csv` (timestamp, reviewer, decision, changes)
- Updated `ledger_classification` for approved items
- Rule suggestions (optional)

---

## Guardrails
- No bulk approvals without explicit reason.
- For high‑risk categories (tax, loans), always require review.
- All decisions logged to `agent.persist`.
