# Ledger Rules (Wireframe)

## Categories
- Revenue
  - Customer Payments
  - Change Orders
  - Draws
- Materials
  - Lumber
  - Concrete
  - Windows/Doors
  - Roofing
  - Electrical
  - Plumbing
  - HVAC
- Labor
  - Payroll Wages
  - Payroll Taxes
  - Benefits
  - Subcontractor Labor
- Equipment
  - Rentals
  - Repairs
  - Fuel
- Overhead
  - Insurance
  - Permits
  - Office
  - Software
  - Marketing
  - Professional Services
- Financing
  - Loan Payments
  - Interest
  - Banking Fees
- Owner
  - Owner Draw
  - Capital Contribution
- Taxes
  - Sales Tax
  - Payroll Tax
  - Income Tax

## Rule Precedence
1. Exact match (vendor + memo)
2. Vendor map
3. Cost code map
4. Regex match
5. Contains match
6. Phase hint

## Confidence Logic
- Exact match: 0.98
- Vendor map: 0.90
- Cost code map: 0.92
- Regex match: 0.85
- Contains match: 0.75
- Phase hint only: 0.60

Manual review if:
- Confidence < 0.85
- Category is Taxes or Financing
- No match found

## Example Rules
- Vendor: "Home Depot" -> Materials / Lumber
- Vendor: "Lowe's" -> Materials / Electrical
- Vendor: "ABC Concrete" -> Materials / Concrete
- Vendor: "United Rentals" -> Equipment / Rentals
- Memo contains "PAYROLL" -> Labor / Payroll Wages
- Memo contains "ADP" -> Labor / Payroll Taxes
- Memo contains "INSURANCE" -> Overhead / Insurance
- Memo contains "PERMIT" -> Overhead / Permits
- Vendor contains "IRS" -> Taxes / Payroll Tax (review required)
- Memo contains "INTEREST" -> Financing / Interest (review required)

## Notes
- Keep vendor list normalized (strip punctuation, lowercase).
- Prefer job/cost-code mappings when present.
- Update rules based on approved review outcomes.

---

## Expanded Ledger Taxonomy & Rule Logic

### Categories & Subcategories

- **Income**
  - Customer Payments
  - Change Orders
  - Draws
  - Refunds & Rebates
- **Materials**
  - Lumber
  - Concrete
  - Windows/Doors
  - Roofing
  - Electrical
  - Plumbing
  - HVAC
- **Labor**
  - Payroll Wages
  - Payroll Taxes
  - Benefits
  - Subcontractor Labor
- **Equipment**
  - Rentals
  - Repairs
  - Fuel
- **Overhead**
  - Insurance
  - Permits
  - Office
  - Software
  - Marketing
  - Professional Services
- **Financing**
  - Loan Payments
  - Interest
  - Banking Fees
- **Owner**
  - Owner Draw
  - Capital Contribution
- **Taxes**
  - Sales Tax
  - Payroll Tax
  - Income Tax

### Rule Precedence

1. **Manual overrides**: tagged as `manual_override`.
2. **Vendor match**: exact vendor + memo.
3. **Cost code mapping**: if present.
4. **Regex match**: high-specificity rules.
5. **Contains match**: general matches.
6. **Phase hint**: fallback when metadata exists.

### Confidence Thresholds

- **0.90-1.00**: auto-apply, no review.
- **0.85-0.89**: apply, flag background review.
- **<0.85**: manual review required.

### Review Triggers

- New/unclassified vendors.
- Conflicting rule matches with similar confidence.
- High-value transactions (e.g., > $10,000).
- Categories: Taxes, Financing, Owner.
- Negative balances or reversals.

## Appendix: Example Rule Table

| Pattern                 | Category         | Confidence | Review |
|-------------------------|------------------|------------|--------|
| HOME DEPOT              | Materials        | 1.0        | false  |
| LOWE.*S                 | Materials        | 1.0        | false  |
| UNITED RENTALS          | Equipment Rental | 1.0        | false  |
| SUNBELT RENTALS         | Equipment Rental | 1.0        | false  |
| FASTENAL                | Materials        | 0.95       | false  |
| GRAINGER                | Materials        | 0.90       | false  |
| ACME PLUMBING           | Plumbing         | 0.95       | false  |
| SUPERIOR ELECTRIC       | Electrical       | 0.95       | false  |
| ROBERTSON DRYWALL       | Drywall          | 1.0        | false  |
| TRI-COUNTY GLASS        | Windows/Doors    | 1.0        | false  |
| TEMP LABOR              | Labor            | 0.85       | true   |
| UNKNOWN VENMO           | Miscellaneous    | 0.70       | true   |
| ROTO-ROOTER             | Plumbing         | 0.98       | false  |
| STAR CONSTRUCTION CLEAN | Cleaning         | 0.90       | false  |
| WALMART                 | Supplies         | 0.85       | true   |

## Appendix: Example Rule Format (YAML)

```yaml
- pattern: "HOME DEPOT"
  category: Materials
  confidence: 1.0
  review: false

- pattern: "^TEMP LABOR"
  category: Labor
  confidence: 0.85
  review: true

- pattern: "UNKNOWN VENMO"
  category: Miscellaneous
  confidence: 0.7
  review: true
```

## Review Protocol

- All entries with `review: true` require manual review/approval before posting.
- Entries with low confidence or ambiguous descriptions should trigger alerts for new rule addition/exception handling.

## Appendix: Construction Vendor Patterns (Draft)

Note: Map these to the taxonomy before automation.

| Pattern                | Category         | Confidence | Review |
|------------------------|------------------|------------|--------|
| FASTENAL               | Materials        | 0.95       | false  |
| SQUARESPACE MATERIALS  | Materials        | 0.90       | true   |
| ACE HARDWARE           | Materials        | 0.95       | false  |
| ROYAL CONCRETE         | Materials        | 1.00       | false  |
| METRO GLASS            | Windows/Doors    | 0.98       | false  |
| SUPERIOR ELECTRIC      | Electrical       | 1.00       | false  |
| CITY INSPECTION        | Overhead/Permits | 0.90       | true   |
| TEMP STAFF SOLUTIONS   | Labor            | 0.85       | true   |
| BLUE STAR ROOFING      | Roofing          | 0.95       | false  |
| JOHNSON HVAC           | HVAC             | 1.00       | false  |
| BUILDERS WASTE REMOVAL | Overhead/Disposal| 0.95       | false  |
| CLIENT REIMBURSEMENT   | Owner/Draw       | 0.80       | true   |
