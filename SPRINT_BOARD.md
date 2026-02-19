# Sprint Board

**Lane Summaries (2026-02-18)**
- Infra Lane: Monorepo CI/CD plan with path filters, matrix builds, patch deploy, and manual promote for App Engine services.
- Product Lane: Suite-shell UX with top bar + side app dock, app routing, and lazy module loading.
- Finance Lane: Ledger taxonomy v1, manual review triggers, and cash flow phase mapping by construction phase.
- Scout Lane: Repo inventory template; only payroll partially filled; needs crawl of all JCW repos.
- Research Lane: 5 agentic modeling spikes; sources require verification before adoption.

---

**Ready**
- Infra: Draft monorepo directory layout under `services/` with payroll, estimating, financials, suite-shell. Acceptance: repo layout doc + directories created.
- Product: Build suite-shell skeleton UI with app buttons and routing stub. Acceptance: app dock renders and routes to placeholder pages.
- Research: Verify sources and convert 5 spikes into full spike docs with evidence. Acceptance: 5 spike files in `research/spikes/`.

**In Progress**
- Infra: Implement GitHub Actions matrix workflow with path filters and App Engine patch/promote per service. Acceptance: `infra/ci-cd-monorepo.yml` added.
- Scout: Create repo inventory and populate all JCW repos. Acceptance: table with stack, deploy, datastore, owners, risks.
- Ops Agent (Dashboard): Ship suite ops dashboard `/suite` with sprint/backlog/ops panels. Acceptance: `/suite` loads with live data.
- Ops Agent (Monitor): 15-min monitor timer + status report. Acceptance: timer active + Slack report every 15m.
- Ops Agent (Payroll): Payroll reconcile script against exports + app.db. Acceptance: script runs and outputs week summary.

**Blocked**
- None

**Done**
- Finance: Ledger taxonomy v1 published (`finance/ledger_taxonomy_v1.md`).
- Finance: Manual review queue spec published (`finance/manual_review_queue.md`).
- Finance: Cash flow phase mapping published (`finance/cash_flow_phase_mapping.md`).
- Infra: Monorepo plan drafted (`infra/monorepo_plan.md`).
- Product: Suite-shell UX spec drafted (`product/suite_shell_spec.md`).
- Scout: Initial repo inventory drafted (`inventory/repo_inventory.md`).
