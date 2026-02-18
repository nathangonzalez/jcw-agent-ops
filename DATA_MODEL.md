# Data Model (Wireframe)

## Purpose
Define the core data structures for ledger classification, manual review, and cash‑flow analysis across the JCW enterprise suite.

---

## 1) Transactions
**Source**: bank feeds, card transactions, invoices, bills, payroll, estimator line items.  
**Granularity**: single transaction (debit/credit).

**Fields**
- `transaction_id` (string, stable)
- `date` (YYYY‑MM‑DD)
- `amount` (number, signed)
- `currency` (string, e.g., USD)
- `merchant` (string, raw)
- `description` (string, raw)
- `account_id` (string)
- `account_type` (enum: checking, savings, credit, loan)
- `source_system` (enum: bank, card, payroll, estimator, ap, ar)
- `job_id` (string, optional)
- `cost_code` (string, optional)
- `phase` (enum: precon, foundation, framing, MEP, windows, finishes, closeout)
- `counterparty` (string, optional)
- `tags` (array of strings)

---

## 2) Ledger Classification
**Goal**: map each transaction into a standard ledger entry.

**Fields**
- `ledger_id` (string)
- `category` (string, e.g., Materials, Labor, Subcontractor, Equipment, Overhead)
- `subcategory` (string, e.g., Lumber, HVAC, Payroll Taxes, Tool Rental)
- `confidence` (0‑1)
- `rule_id` (string, optional)
- `reason` (string, human‑readable)
- `review_required` (boolean)
- `review_status` (enum: pending, approved, rejected)
- `review_notes` (string, optional)

---

## 3) Rules
**Rule types**: exact match, contains, regex, vendor map, cost code map, phase map.

**Fields**
- `rule_id` (string)
- `priority` (integer, higher wins)
- `match_type` (enum: exact, contains, regex, vendor, cost_code, phase)
- `match_value` (string)
- `category` / `subcategory` (strings)
- `confidence_boost` (number)
- `requires_review` (boolean)
- `applies_to` (enum: all, bank, card, payroll, estimator)

---

## 4) Manual Review Queue
**Purpose**: human review for low confidence or ambiguous entries.

**Fields**
- `review_id` (string)
- `transaction_id` (string)
- `proposed_category` (string)
- `confidence` (0‑1)
- `review_reason` (string)
- `created_at` (timestamp)
- `assigned_to` (string, optional)
- `status` (enum: pending, approved, rejected, deferred)
- `resolution` (string, optional)

---

## 5) Cash‑Flow Cycle Mapping
**Purpose**: link transactions to construction phases and expected cash patterns.

**Fields**
- `phase` (enum)
- `phase_start` / `phase_end` (dates)
- `expected_inflows` (range)
- `expected_outflows` (range)
- `variance` (number)
- `notes` (string)

---

## 6) Integration Points

**Payroll**
- Map payroll runs to `Labor` + job/phase.
- Identify burden (taxes, benefits) separately.

**Estimator**
- Convert estimate line items into expected phase costs.
- Compare actuals to estimates per phase.

**3D Studio**
- Map design milestones to phase triggers (precon → foundation).

---

## 7) Outputs (for agents)
- Daily classification report
- Review queue (CSV/JSON)
- Phase cash‑flow variance report
- Top cost overruns and savings opportunities
