# Sprint Board

**Lane Summaries (2026-02-20)**
- Infra Lane: Updated monorepo CI/CD plan with path filters, matrix builds, patch deploy, and manual promote for App Engine services (minimal YAML outline ready).
- Product Lane: Suite-shell UX draft with top bar + left rail app dock, routing, and lazy module loading.
- Finance Lane: Ledger taxonomy v1, manual review triggers, and cash flow phase mapping by construction phase (expanded detail).
- Scout Lane: Repo inventory refreshed; still only partially populated and needs crawl of all JCW repos.
- Research Lane: 5 agentic modeling spikes drafted; sources require verification before adoption.

---

**Ready**
- Ops Agent (Relay): Stabilize Slack Relay. Ensure 100% reliable chat interface via Slack, fixing missing messages. Acceptance: Chatting with @jcw_service works reliably without dropping context.
- Product: Build suite-shell skeleton UI with app buttons and routing stub. Acceptance: app dock renders and routes to placeholder pages.

**Backlog (Needs Refinement)**
- Infra: Office Server Cloud Backup — Install rclone on office server, configure nightly sync to GCS bucket `gs://jcw-office-backup/`, schedule via Windows Task Scheduler. Acceptance: nightly backup runs, QuickBooks + shared files in GCS, restore tested.
- Infra: Migrate Shared Files to Google Drive — Move office shared folders to a Google Workspace Shared Drive. Staff accesses via browser/Drive app, no VPN needed for files. Acceptance: all shared folders on Google Drive, staff trained, old server shares read-only.
- Infra: QuickBooks Migration Assessment — Evaluate QB Desktop → QB Online migration path. Document data migration steps, cost impact, training needs. Acceptance: decision doc with recommendation + timeline.
- Infra: Labor Timekeeper to Persistent VM — Move labor-timekeeper from App Engine (ephemeral SQLite) to GCE VM with persistent disk + Docker. Acceptance: app runs on VM, DB survives deploys, automated backup to GCS.
- Ops Agent (24/7): VM Agent Hardening — Cline running on clawbot-ops via VS Code Tunnel with .clinerules guardrails. Heartbeat checks, spending caps, kill switch via Slack. Acceptance: agent runs 24/7, responds to /kill, stays within $5/day budget.

**In Progress**
- Infra: Implement GitHub Actions matrix workflow with path filters and App Engine patch/promote per service. Acceptance: `infra/ci-cd-monorepo.yml` added.
- Scout: Create repo inventory and populate all JCW repos (refreshed; still partial). Acceptance: table with stack, deploy, datastore, owners, risks.
- Ops Agent (Dashboard): Ship suite ops dashboard `/suite` with sprint/backlog/ops panels. Acceptance: `/suite` loads with live data.
- Ops Agent (Suite Shell): JCW app store UI (app cards + routing links). Acceptance: app grid renders from `/api/apps`.
- Ops Agent (Approvals): Approval queue + scheduled Slack prompts. Acceptance: pending approvals auto-post to Slack with buttons.
- Ops Agent (Monitor): 15-min monitor timer + status report. Acceptance: timer active + Slack report every 15m.
- Ops Agent (Payroll): Payroll reconcile script against exports + app.db. Acceptance: script runs and outputs week summary.
- Ops Agent (Metrics): Firestore metrics + suite dashboard usage panel. Acceptance: `/suite` shows token + VM stats.

**Blocked**
- None

**Done**
- Finance: Billing = Payroll Logic Parity — DB-managed `client_bill_rate` column, `buildBillingRatesMap()` replaces hardcoded rates (commit `0d3eb72`, 2026-02-22).
- Finance: Timesheet Formatting Fixes — consistent borders, spacing, Boban gap fixed (commit `89eced8`, 2026-02-22).
- Product: JCW Website Redesign — design brief + sitemap published (`docs/JCW_WEBSITE_REDESIGN_BRIEF.md`, commit `b0a41dd`, 2026-02-22).
- Infra: Monorepo directory layout — `services/` dirs + READMEs created (2026-02-22).
- Research: 5 spike docs verified and published to `research/spikes/` (2026-02-22).
- Finance: Ledger taxonomy v1 published (`finance/ledger_taxonomy_v1.md`).
- Finance: Manual review queue spec published (`finance/manual_review_queue.md`).
- Finance: Cash flow phase mapping published (`finance/cash_flow_phase_mapping.md`).
- Infra: Monorepo plan drafted (`infra/monorepo_plan.md`).
- Product: Suite-shell UX spec drafted (`product/suite_shell_spec.md`).
- Scout: Initial repo inventory drafted (`inventory/repo_inventory.md`).
- Scout: Repo inventory refreshed (`inventory/repo_inventory.md`).
