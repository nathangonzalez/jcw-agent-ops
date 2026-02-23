# Sprint Board

**Lane Summaries (2026-02-23)**
- Infra Lane: CI/CD monorepo workflow shipped. QB Migration Assessment and Labor Timekeeper VM Migration plans complete.
- Product Lane: Suite-shell UX draft with top bar + left rail app dock, routing, and lazy module loading.
- Finance Lane: Billing parity, timesheet fixes shipped. Ledger taxonomy, review queue, cash flow mapping published.
- Scout Lane: Repo inventory COMPLETE — all 19 repos crawled with stack, deploy target, risks.
- Ops Lane: Slack relay stabilization plan with 9 fixes documented. VM Agent hardening partially complete (tunnel + Cline running).
- Research Lane: Story generator + research digest workflows running on schedule.

---

**Ready**
- Ops Agent (Relay): Stabilize Slack Relay. Ensure 100% reliable chat interface via Slack, fixing missing messages. Acceptance: Chatting with @jcw_service works reliably without dropping context.
- Product: Build suite-shell skeleton UI with app buttons and routing stub. Acceptance: app dock renders and routes to placeholder pages.

**Backlog (Needs Refinement)**
- Infra: Office Server Cloud Backup — Install rclone on office server, configure nightly sync to GCS bucket `gs://jcw-office-backup/`, schedule via Windows Task Scheduler. Acceptance: nightly backup runs, QuickBooks + shared files in GCS, restore tested.
- Infra: Migrate Shared Files to Google Drive — Move office shared folders to a Google Workspace Shared Drive. Staff accesses via browser/Drive app, no VPN needed for files. Acceptance: all shared folders on Google Drive, staff trained, old server shares read-only.

**In Progress**
- Infra: Labor Timekeeper to Persistent VM — Migration plan written (`docs/labor_timekeeper_vm_migration.md`). Next: implement Docker changes and deploy. Acceptance: app runs on VM, DB survives deploys.
- Ops Agent (Relay): Stabilization plan written (`docs/slack_relay_stabilization.md`). Next: implement 9 code fixes. Acceptance: reliable Slack relay.
- Ops Agent (24/7): VM Agent Hardening — Tunnel running, Cline installed, .clinerules in place. Next: heartbeat checks, spending monitoring. Acceptance: agent runs 24/7, responds to /kill.
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
- Scout: Repo inventory COMPLETE — all 19 repos crawled with stack, deploy, datastore, risks (`inventory/repo_inventory.md`, commit `f562cca`, 2026-02-23).
- Infra: QuickBooks Migration Assessment — QBO Plus recommended, 4-phase timeline, construction-specific analysis (`docs/QUICKBOOKS_MIGRATION_ASSESSMENT.md`, commit `f562cca`, 2026-02-23).
- Infra: CI/CD Monorepo Workflow — 5-job pipeline with path filters, matrix builds, no-promote deploy, manual promote gate (`.github/workflows/ci-cd-monorepo.yml`, commit `f562cca`, 2026-02-23).
- Infra: Labor Timekeeper VM Migration Plan — Docker config, 4-phase migration, backup strategy, rollback plan (`docs/labor_timekeeper_vm_migration.md`, commit `8286093`, 2026-02-23).
- Ops: Slack Relay Stabilization Plan — 9 reliability issues identified with code-level fixes (`docs/slack_relay_stabilization.md`, commit `f562cca`, 2026-02-23).
- Ops: VM Agent Hardening (partial) — VS Code Tunnel running, Cline installed, .clinerules + TRAINING.md published (2026-02-23).
