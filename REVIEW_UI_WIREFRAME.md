# Review Queue UI (Wireframe)

## Layout

Top Bar
- Date range picker
- Filters: vendor, job, phase, category, confidence range
- Search box (merchant/description)
- Export buttons: CSV, JSON

Main Table
- Columns:
  - Date
  - Vendor
  - Amount
  - Proposed Category
  - Confidence
  - Reason
  - Status
  - Actions

Actions
- Approve
- Reject
- Escalate
- Override Category (dropdown)
- Add Note
- Defer

Right Panel (Detail)
- Raw transaction
- Suggested ledger fields
- History of edits
- Related transactions (same vendor)

---

## Additional UI Notes

- Header actions: Refresh, Filters
- Bulk actions: Approve Selected, Reject Selected, Escalate
- States: Idle, Loading, Empty, Error, Confirmation
- Logging: record reviewer, timestamp, action, and notes

## Flow
1. Row selected -> detail panel opens
2. Reviewer approves/rejects/overrides
3. Decision logged to agent.persist
4. Rule suggestion generated (optional)

## States
- Pending
- Approved
- Rejected
- Deferred

## Minimal Data Fields
- transaction_id
- date
- amount
- merchant
- description
- category/subcategory
- confidence
- review_status
- review_notes
