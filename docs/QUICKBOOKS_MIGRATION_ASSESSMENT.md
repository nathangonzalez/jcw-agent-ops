# QuickBooks Migration Assessment — JCW Construction

**Prepared by:** Infra Agent  
**Date:** 2026-02-23  
**Status:** DRAFT — Pending Owner Review  
**Audience:** Nathan Gonzalez (IT/Operations), Chris Jacobi (Owner/Admin)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Assessment](#2-current-state-assessment)
3. [Migration Options](#3-migration-options)
4. [Data Migration](#4-data-migration--what-transfers-and-what-doesnt)
5. [Cost Comparison](#5-cost-comparison)
6. [Pros and Cons Matrix](#6-pros-and-cons-matrix)
7. [Risk Assessment](#7-risk-assessment)
8. [Prerequisites and Preparation](#8-prerequisites-and-preparation)
9. [Recommendation](#9-recommendation)
10. [Implementation Timeline](#10-implementation-timeline)
11. [Appendices](#11-appendices)

---

## 1. Executive Summary

JCW Construction currently runs QuickBooks Desktop on an on-premise Windows server. As the company moves toward cloud infrastructure (SharePoint migration, GCP-hosted labor timekeeper, Slack-based ops), the accounting system is the last major on-premise dependency. This document evaluates three paths forward: migrating to QuickBooks Online (QBO), hosting QuickBooks Desktop in the cloud via a third-party provider, or a hybrid approach.

**Bottom line:** We recommend **QuickBooks Online Plus** as the primary target, with a phased migration starting in Q2 2026. QBO aligns with JCW’s cloud-first direction, eliminates VPN/server maintenance overhead, and integrates natively with the labor timekeeper and future billing modules. A 90-day migration window with parallel operation minimizes risk.

---

## 2. Current State Assessment

### 2.1 Infrastructure

| Component | Current State |
|-----------|--------------|
| **Software** | QuickBooks Desktop (Pro or Premier — verify edition) |
| **Server** | On-premise Windows Server (local office network) |
| **Backup** | Manual backups (ad-hoc .QBB files to local/external drive) |
| **Remote Access** | VPN required for off-site access |
| **Users** | ~2–4 concurrent (admin + bookkeeper + owner) |
| **Company File Size** | TBD — verify .QBW file size (migration limits apply) |

### 2.2 Current Workflow

- **Payroll:** Managed via JCW Labor Timekeeper (cloud PWA) → XLSX export → manual entry into QB Desktop. 8 employees, weekly timesheets, monthly billing cycles.
- **Job Costing:** Construction job costing using QB Desktop job/customer hierarchy. 93+ active customers/projects.
- **Accounts Payable:** Vendor bills entered manually. Subcontractor payments tracked per project phase.
- **Accounts Receivable:** Progress billing / draw requests tied to construction phases (preconstruction through closeout).
- **Reporting:** Standard P&L, Balance Sheet, Job Cost reports. Likely includes custom reports for construction-specific views.
- **Integrations:** No known direct API integrations with QB Desktop (data flows are manual/XLSX-based).

### 2.3 Pain Points

| Pain Point | Impact |
|------------|--------|
| VPN required for remote QB access | Slows field/remote work, single point of failure |
| Manual backups | Risk of data loss; no offsite/automated backup |
| Server maintenance overhead | Patching, hardware lifecycle, power/network dependency |
| Manual payroll data entry | Double-entry from timekeeper → QB; error-prone |
| No real-time multi-user collaboration | File locking issues, version conflicts |
| Disconnected from cloud stack | Labor timekeeper, Slack ops, SharePoint are all cloud — QB is the gap |

---

## 3. Migration Options

### Option A: QuickBooks Online (QBO)

Full migration from QuickBooks Desktop to QuickBooks Online. Company file is converted and all future work happens in QBO.

**Best for:** Companies moving to cloud-first, wanting API integrations, multi-location access.

### Option B: QuickBooks Desktop Hosted (Cloud Desktop)

Keep QuickBooks Desktop software but move it to a hosted environment (Right Networks, Swizznet, Summit Hosting, etc.). Access via Remote Desktop / thin client.

**Best for:** Companies with heavy Desktop customization, complex inventory, or third-party Desktop-only plugins they cannot abandon.

### Option C: Hybrid Approach

Migrate to QBO for day-to-day operations but keep a read-only Desktop archive for historical data and legacy report access. Run parallel for 1–2 quarters before full cutover.

**Best for:** Risk-averse migration with a safety net. This is our recommended approach.

---

## 4. Data Migration — What Transfers and What Doesn’t

### 4.1 What Migrates to QBO

| Data Type | Migration Support | Notes |
|-----------|-------------------|-------|
| Chart of Accounts | ✅ Full | Transfers with account types. Review for cleanup opportunity. |
| Customer list | ✅ Full | Names, addresses, contact info, balances |
| Vendor list | ✅ Full | Names, addresses, contact info, balances |
| Employee list | ✅ Full | Basic info transfers; payroll details require re-setup |
| Items / Services list | ✅ Full | Service items, inventory items, non-inventory items |
| Open invoices | ✅ Full | Unpaid/partially paid invoices |
| Open bills | ✅ Full | Unpaid/partially paid vendor bills |
| Open purchase orders | ✅ Full | Outstanding POs |
| Bank account balances | ✅ Full | As of migration date |
| Journal entries | ✅ Full | Historical journal entries |
| Checks and deposits | ✅ Full | Historical transactions |
| Estimates | ✅ Full | Open estimates transfer |

### 4.2 What Does NOT Migrate (or Migrates Partially)

| Data Type | Migration Support | Workaround |
|-----------|-------------------|------------|
| **Custom reports** | ❌ Does not transfer | Rebuild in QBO. Document current custom reports before migration. |
| **Memorized transactions** | ❌ Does not transfer | Recreate as Recurring Transactions in QBO. |
| **Reconciliation history** | ⚠️ Partial | Reconciliation status transfers but not the detail. Print/PDF all reconciliation reports before migration. |
| **Payroll history** | ⚠️ Partial | YTD payroll totals may need manual re-entry. Prior year W-2 data does not migrate. |
| **Audit trail** | ❌ Does not transfer | Export audit log from Desktop before migration. |
| **Attachments** | ❌ Does not transfer | Must be manually re-uploaded or stored in SharePoint. |
| **Custom fields** | ⚠️ Limited | QBO has fewer custom field options. Map custom fields to QBO equivalents or use tags. |
| **Job costing hierarchy** | ⚠️ Changed | QB Desktop sub-jobs become sub-customers in QBO. Structure is preserved but terminology changes. |
| **Budget data** | ⚠️ Partial | May need re-entry depending on complexity. |
| **Sales tax settings** | ⚠️ Partial | QBO uses automated sales tax; manual rates need reconfiguration. |
| **Third-party app data** | ❌ Varies | Each integration must be evaluated separately. |

### 4.3 Construction-Specific Migration Concerns

- **Job Costing:** QB Desktop’s Job:Phase:Cost Code hierarchy (Customer:Job:Sub-item) maps to QBO’s Customer:Sub-customer:Product/Service structure. The mapping works but requires careful planning.
- **Progress Invoicing:** QBO supports progress invoicing but the workflow differs from Desktop. Test with a sample project before full migration.
- **Change Orders:** If tracked as estimates in Desktop, they transfer. If tracked via custom fields or memorized transactions, they need manual recreation.
- **Retention/Retainage:** QBO does not natively handle retainage. Consider a third-party app (e.g., Siteline, Knowify, or Buildertrend integration) or manual tracking.
- **Certified Payroll / Prevailing Wage:** If JCW does public/government work, verify that QBO payroll or a connected service handles certified payroll (Davis-Bacon compliance).
- **AIA Billing (G702/G703):** QBO does not produce AIA billing forms natively. Use a construction-specific add-on (Knowify, Buildertrend, CoConstruct) or continue generating AIA forms externally.

---

## 5. Cost Comparison

### 5.1 Current Costs (QB Desktop On-Premise)

| Cost Item | Estimated Annual Cost |
|-----------|-----------------------|
| QB Desktop Pro/Premier license (one-time, amortized 3 years) | $150–250/year |
| Server hardware maintenance/replacement (amortized) | $500–1,000/year |
| Windows Server license (if applicable) | $300–500/year |
| Backup solution (if any) | $0–200/year |
| VPN service/hardware | $100–300/year |
| IT support time (patching, troubleshooting, backups) | $500–2,000/year |
| **Total estimated** | **$1,550–4,250/year** |

### 5.2 Option A: QuickBooks Online

| QBO Plan | Monthly Cost | Annual Cost | Notes |
|----------|-------------|-------------|-------|
| Simple Start | $30/month | $360/year | 1 user. Too limited for construction. |
| Essentials | $60/month | $720/year | 3 users, bill management. Minimum viable. |
| **Plus** | **$90/month** | **$1,080/year** | **5 users, project tracking, inventory. Recommended.** |
| Advanced | $200/month | $2,400/year | 25 users, custom roles, dedicated support. |

**Additional QBO costs:**
- QBO Payroll: $50–130/month + $6/employee/month (if moving payroll to QBO)
- Construction add-ons (Knowify, Buildertrend): $100–500/month depending on scope
- Migration service (if using Intuit or third-party): $0–2,000 one-time

### 5.3 Option B: Hosted QB Desktop

| Provider | Monthly Cost | Annual Cost | Notes |
|----------|-------------|-------------|-------|
| Right Networks | $50–80/user/month | $1,800–5,760/year (3 users) | Most popular QB host. Intuit-authorized. |
| Swizznet | $45–70/user/month | $1,620–5,040/year (3 users) | Good mid-tier option. |
| Summit Hosting | $40–65/user/month | $1,440–4,680/year (3 users) | Budget option. |

**Plus:** QB Desktop license still required ($300–650/year for Premier).

### 5.4 Cost Summary

| Option | Year 1 Cost (incl. migration) | Ongoing Annual Cost |
|--------|-------------------------------|---------------------|
| **Stay on-premise** | $1,550–4,250 | $1,550–4,250 |
| **QBO Plus** | $2,080–4,080 (incl. migration) | $1,080–1,800 |
| **Hosted Desktop** | $3,200–6,500 | $3,200–6,500 |

**QBO has the lowest ongoing cost and eliminates server maintenance entirely.**

---

## 6. Pros and Cons Matrix

### Option A: QuickBooks Online (QBO)

| Pros | Cons |
|------|------|
| Access from anywhere — no VPN needed | Feature differences from Desktop (learning curve) |
| Automatic updates and backups | Limited custom report builder vs Desktop |
| Native API for integrations (labor timekeeper, Slack) | Retainage not natively supported |
| Real-time multi-user collaboration | Subscription cost is ongoing (no perpetual license) |
| Mobile app for field access | Company file size/history limits on some plans |
| Integrates with 750+ apps | Some Desktop workflows don’t have QBO equivalents |
| Lowest ongoing cost | Internet required (no offline mode) |
| Bank feeds / auto-categorization | Migration is one-way — cannot go back to Desktop easily |
| Scales with cloud-first strategy | |

### Option B: Hosted QB Desktop

| Pros | Cons |
|------|------|
| Keep existing Desktop workflows exactly | Higher ongoing cost than QBO |
| No retraining needed | Still requires Desktop license purchase |
| Desktop-only plugins continue to work | Remote Desktop UX is clunky (latency, printing issues) |
| Hosted backups included | No native API (still manual data flows) |
| No migration risk (same software) | Vendor lock-in to hosting provider |
| | Server is cloud but workflow is still Desktop-era |
| | Does not solve the integration gap with labor timekeeper |

### Option C: Hybrid (Recommended)

| Pros | Cons |
|------|------|
| Safety net — Desktop available during transition | Dual system cost during parallel period |
| Gradual learning curve for staff | Requires discipline to enter data in QBO (not fall back to Desktop) |
| Can validate QBO data against Desktop | 1–2 quarter overhead of running both |
| Rollback possible during parallel period | |
| Historical data preserved in Desktop archive | |

---

## 7. Risk Assessment

### 7.1 Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Data loss during migration** | Low | Critical | Full backup before migration. Verify data post-migration line by line for first month. Keep Desktop archive. |
| **Incomplete data transfer** | Medium | High | Use Intuit migration tool. Document all custom reports, memorized transactions, and custom fields beforehand. |
| **Job costing structure breaks** | Medium | High | Map Customer:Job hierarchy to QBO Sub-customer structure before migration. Test with 2–3 sample jobs. |
| **Retainage tracking gap** | High | Medium | Evaluate construction add-ons (Knowify, Buildertrend). Implement workaround before migration. |
| **Staff resistance / training gap** | Medium | Medium | Hands-on training sessions. Run parallel for 1 quarter. Identify QBO champion on team. |
| **Downtime during cutover** | Low | Medium | Migrate on weekend. Target end of month/quarter for clean cutover point. |
| **Integration failures** | Low | Medium | Test labor timekeeper → QBO API flow in sandbox before production migration. |
| **Payroll disruption** | Medium | Critical | If using QB payroll: migrate payroll at quarter boundary (Q3 start). Verify YTD totals. Consider keeping payroll on Desktop one extra quarter. |
| **Internet outage = no access** | Low | Medium | QBO has limited offline capability. Maintain mobile hotspot as backup. |
| **Vendor/sub payment disruption** | Low | High | Verify all open bills, POs, and vendor credits transfer. Reconcile AP aging before and after. |

### 7.2 Construction-Specific Risks

- **Mid-project migration:** Migrating during active projects means open estimates, invoices, and job costs must transfer cleanly. Never migrate mid-draw-request-cycle.
- **Lien waiver tracking:** If tracked in QB Desktop, verify the tracking method transfers or set up in QBO/SharePoint.
- **Workers comp audit:** Ensure payroll classifications and workers comp codes are preserved or recreated for annual audit.
- **1099 reporting:** Verify vendor 1099 tracking transfers. Migration mid-year requires careful YTD validation.
- **Bonding company requirements:** If JCW is bonded, verify the bonding company accepts QBO reports or can access what they need.

---

## 8. Prerequisites and Preparation

### 8.1 Data Cleanup (Do BEFORE Migration)

This is the most important step. Clean data migrates cleanly. Dirty data creates months of post-migration headaches.

- [ ] **Verify QB Desktop edition and version** — QBO migration tool has version requirements
- [ ] **Check company file size** — Files over 750K targets (transactions + list entries) may hit QBO limits
- [ ] **Clean up Chart of Accounts** — Merge duplicate accounts, inactivate unused accounts, standardize naming convention (e.g., consistent cost code prefixes)
- [ ] **Clean up Customer/Job list** — Merge duplicate customers, inactivate completed jobs (archive, don’t delete), verify Customer:Job:Sub-job hierarchy matches desired QBO structure
- [ ] **Clean up Vendor list** — Merge duplicates, verify 1099 flags on all applicable vendors, update W-9 info
- [ ] **Clean up Item list** — Remove obsolete items, standardize names and descriptions, map service items to QBO Products/Services
- [ ] **Reconcile all bank/credit card accounts** — All accounts must be reconciled to current date
- [ ] **Resolve all open transactions** — Clear old open invoices (write off or collect), clear old open bills, resolve unapplied payments and credits
- [ ] **Export/document everything that will not migrate** — Print all custom reports to PDF, export memorized transaction list, document memorized reports, export audit trail, save all attachments to SharePoint
- [ ] **Verify payroll YTD totals** — Print payroll summary by employee, YTD
- [ ] **Run trial balance** — Save as baseline to verify post-migration

### 8.2 Integration Planning

- [ ] **Labor Timekeeper → QBO API:** Evaluate QBO API for automated time entry import (eliminates manual XLSX → QB entry)
- [ ] **Retainage solution:** Select and test construction add-on for retainage tracking
- [ ] **AIA billing:** Identify tool for AIA G702/G703 form generation
- [ ] **Bank feeds:** Set up bank feed connections in QBO (checking, credit cards, loans)
- [ ] **SharePoint:** Plan document storage strategy (receipts, contracts, lien waivers in SharePoint vs QBO attachments)

### 8.3 Backup Strategy

- [ ] **Full .QBB backup** of company file (store on external drive + cloud)
- [ ] **Full .QBW copy** (working file) as secondary backup
- [ ] **Portable company file** (.QBM) as tertiary backup
- [ ] **Export all lists to CSV/Excel** (Chart of Accounts, Customers, Vendors, Items, Employees)
- [ ] **Export all reports to PDF** (P&L, Balance Sheet, AR/AP Aging, Job Cost, Trial Balance)
- [ ] **Verify backup integrity** — restore test backup on separate machine

---

## 9. Recommendation

### Primary Recommendation: QuickBooks Online Plus (Hybrid Migration)

**Migrate to QBO Plus ($90/month) using a hybrid approach with 90-day parallel operation.**

**Why QBO Plus:**
- 5 users covers JCW’s needs (admin, bookkeeper, owner, + 2 project managers if needed)
- Project tracking feature maps to construction job costing
- API access enables labor timekeeper integration (eliminate manual payroll entry)
- Lowest total cost of ownership
- Aligns with cloud-first direction (SharePoint, GCP labor app, Slack ops)
- Automatic backups eliminate manual backup risk

**Why Hybrid:**
- Zero data loss risk — Desktop archive available for 1–2 quarters post-migration
- Staff can learn QBO while Desktop is still available as safety net
- Historical data accessible in Desktop for lookback / audit purposes
- Rollback option if critical issues discovered

**Why Not Hosted Desktop:**
- Higher cost, same workflow limitations
- No API integration benefit
- Does not solve the core problem (manual data flows, server dependency mindset)

### Secondary Recommendation: Integrate Labor Timekeeper with QBO

Once QBO is live, build a direct integration between the JCW Labor Timekeeper and QBO using the QuickBooks Online API. This eliminates the current manual XLSX export → QB entry workflow and closes the last major automation gap.

**Integration scope:**
- Push approved time entries from labor timekeeper → QBO as time tracking entries
- Map employees, customers (jobs), and service items automatically
- Estimated development: 2–4 weeks for a basic integration module

---

## 10. Implementation Timeline

### Phase 0: Preparation (Weeks 1–4)

| Week | Task | Owner |
|------|------|-------|
| 1 | Verify QB Desktop edition, version, file size | IT |
| 1 | Sign up for QBO Plus (free trial or sandbox) | IT/Admin |
| 1–2 | Data cleanup: Chart of Accounts, Customer/Job list | Bookkeeper + Admin |
| 2–3 | Data cleanup: Vendor list, Item list, reconciliations | Bookkeeper |
| 3 | Document all custom reports, memorized transactions | Bookkeeper |
| 3 | Select retainage/construction add-on for QBO | IT + Admin |
| 4 | Full backup of QB Desktop (3 copies, verified) | IT |
| 4 | Export all lists and reports to PDF/Excel | Bookkeeper |
| 4 | Run and save pre-migration trial balance | Bookkeeper |

### Phase 1: Migration (Week 5 — Target: Weekend)

| Step | Task | Owner |
|------|------|-------|
| Friday PM | Final reconciliation of all accounts | Bookkeeper |
| Friday PM | Final full backup | IT |
| Saturday | Run Intuit migration tool (Desktop → QBO) | IT |
| Saturday | Verify migration: trial balance, AR/AP aging, job list | Bookkeeper + IT |
| Sunday | Set up bank feeds in QBO | IT |
| Sunday | Configure user access and permissions | IT/Admin |
| Sunday | Install construction add-on (retainage) | IT |
| Monday | Staff orientation — basic QBO walkthrough | IT + All users |

### Phase 2: Parallel Operation (Weeks 6–18 / ~90 Days)

| Activity | Details |
|----------|---------|
| **Primary system:** QBO | All new transactions entered in QBO |
| **Secondary system:** QB Desktop (read-only) | Available for historical reference and report comparison |
| **Weekly check** | Compare QBO vs Desktop balances for first 4 weeks |
| **Monthly check** | Run P&L and Balance Sheet in both systems, compare |
| **Training** | Weekly 30-minute QBO tips session for first month |
| **Integration dev** | Build labor timekeeper → QBO API integration during this phase |

### Phase 3: Cutover (Week 19)

| Step | Task |
|------|------|
| Final comparison | Run full financial comparison QBO vs Desktop |
| Archive Desktop | Move QB Desktop file to cold storage (external drive + cloud archive) |
| Decommission server | If QB was the last service on the on-premise server, plan server decommission |
| Go-live confirmation | All users confirmed working in QBO exclusively |
| Integration go-live | Labor timekeeper → QBO integration activated |

### Phase 4: Optimization (Weeks 20–26)

| Task | Details |
|------|---------|
| Build custom reports in QBO | Recreate critical reports from Desktop |
| Refine job costing workflow | Optimize sub-customer / project structure |
| Automate recurring transactions | Set up recurring bills, invoices in QBO |
| Evaluate additional integrations | Receipt capture, expense tracking, estimating → QBO |
| Document new procedures | Update SOPs for QBO workflow |

### Key Milestones

| Date (Target) | Milestone |
|---------------|-----------|
| End of Q1 2026 | Phase 0 complete — data cleaned, backups done |
| Q2 2026 Week 1 | Migration executed (target: April or start of a month) |
| Q2–Q3 2026 | Parallel operation |
| End of Q3 2026 | Full cutover to QBO |
| Q4 2026 | Optimization and integration complete |

---

## 11. Appendices

### Appendix A: QBO Plan Comparison (as of 2026)

| Feature | Simple Start | Essentials | Plus | Advanced |
|---------|-------------|------------|------|----------|
| Users | 1 | 3 | 5 | 25 |
| Income and expenses | Yes | Yes | Yes | Yes |
| Invoice and payments | Yes | Yes | Yes | Yes |
| Bill management | No | Yes | Yes | Yes |
| Multiple users | No | Yes | Yes | Yes |
| Project profitability | No | No | Yes | Yes |
| Inventory tracking | No | No | Yes | Yes |
| Custom user roles | No | No | No | Yes |
| Dedicated account team | No | No | No | Yes |
| Monthly price | $30 | $60 | $90 | $200 |

### Appendix B: Construction Add-On Options for QBO

| Add-On | What It Solves | Cost Estimate |
|--------|---------------|---------------|
| **Knowify** | Job costing, AIA billing, retainage, change orders | $149–349/month |
| **Buildertrend** | Full project management + accounting sync | $199–599/month |
| **CoConstruct** | Residential builder management + QB sync | $99–399/month |
| **Siteline** | AIA billing / payment applications | Contact for pricing |
| **Expensify** | Receipt capture and expense management | $5/user/month |

### Appendix C: Pre-Migration Checklist (Printable)

```
PRE-MIGRATION CHECKLIST — JCW CONSTRUCTION

[ ] QB Desktop edition and version confirmed: _______________
[ ] Company file size verified: _______________ (targets: _____)
[ ] Chart of Accounts cleaned (duplicates merged, unused inactivated)
[ ] Customer/Job list cleaned (93 customers verified)
[ ] Vendor list cleaned (1099 flags verified)
[ ] Item list cleaned
[ ] All bank accounts reconciled through: ___/___/______
[ ] All credit card accounts reconciled through: ___/___/______
[ ] Open invoices reviewed (old items resolved)
[ ] Open bills reviewed (old items resolved)
[ ] Unapplied payments/credits resolved
[ ] Custom reports documented and exported to PDF
[ ] Memorized transactions documented
[ ] Audit trail exported
[ ] Attachments saved to SharePoint
[ ] Payroll YTD verified by employee
[ ] Pre-migration trial balance saved
[ ] Full .QBB backup created and verified
[ ] Backup copy stored offsite (cloud)
[ ] QBO Plus account provisioned
[ ] Construction add-on selected: _______________
[ ] Migration date confirmed: ___/___/______

Prepared by: _________________ Date: ___/___/______
Verified by: _________________ Date: ___/___/______
```

### Appendix D: Related JCW Infrastructure

| System | Location | Status | Integration with QBO |
|--------|----------|--------|---------------------|
| JCW Labor Timekeeper | GCP App Engine (us-central1) | Production (jcw13) | Target: API integration in Phase 2 |
| Slack Ops (Clawdbot) | GCP VM (clawbot-ops) | Production | Future: financial alerts channel |
| SharePoint | Microsoft 365 | Migration in progress | Document storage for receipts, contracts |
| Email | Microsoft 365 | Production | QBO invoice delivery |

---

*This document is a living assessment. Update as decisions are made and new information becomes available.*

*Last updated: 2026-02-23*
