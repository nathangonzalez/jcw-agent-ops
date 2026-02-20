#!/usr/bin/env bash
set -euo pipefail

OUT_ROOT="${1:-/opt/agent-ops/agent_outputs}"
LANE_AGENT="${CLAW_LANE_AGENT:-main}"
ts="$(date -u +%Y%m%d-%H%M%S)"
outdir="${OUT_ROOT}/lanes_${ts}"
mkdir -p "$outdir"

openclaw agent --agent "$LANE_AGENT" --message "Infra Lane: Draft a monorepo CI/CD plan for App Engine services with patch deploy + promote. Include path filters, matrix strategy, and a minimal YAML outline. Focus on payroll, estimating, financials, suite-shell. Output concise markdown." --thinking low > "${outdir}/lane_infra.md"
openclaw agent --agent "$LANE_AGENT" --message "Product Lane: Define suite-shell UX for a single UI with app buttons. Provide nav structure, modules list, and routing options. Output concise markdown." --thinking low > "${outdir}/lane_product.md"
openclaw agent --agent "$LANE_AGENT" --message "Finance Lane: Draft ledger taxonomy v1 + manual review triggers + cash flow phase mapping. Output headings and bullets." --thinking low > "${outdir}/lane_finance.md"
openclaw agent --agent "$LANE_AGENT" --message "Scout Lane: Create repo inventory template and populate any entries you can from local context. Include stack, deploy method, datastore, owners, risks. Output markdown table." --thinking low > "${outdir}/lane_scout.md"
openclaw agent --agent "$LANE_AGENT" --message "Research Lane: Build a short backlog of 5 agentic modeling spikes (papers/podcasts/tools). Include goal, hypothesis, evaluation, and minimal source list. Output concise markdown." --thinking low > "${outdir}/lane_research.md"

echo "Lane outputs written to ${outdir}"
