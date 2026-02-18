# Manual Review Queue Spec

## Trigger Conditions
- Unusually large or out-of-sequence payments
- Advance/vendor deposits >25% of contract
- Duplicate invoice numbers or dates
- Unregistered or new vendors added
- Unbudgeted change orders
- Missing lien waivers on payment
- Payments made without matching delivery/inspection
- Phase overspend >10% budget
- Requests to release retainage prematurely

## Review States
1. **Queued**: awaiting review
2. **In Review**: reviewer assigned
3. **Needs Info**: missing doc or clarification
4. **Approved**: allowed to post
5. **Rejected**: blocked and flagged

## Outputs
- Decision log with reason
- Links to documents (invoice, waiver, PO)
- Adjusted ledger category (if changed)

## Acceptance
- Every trigger produces a review item
- Each item has a final decision and rationale
