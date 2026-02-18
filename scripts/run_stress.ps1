param(
    [string]$OutputRoot = "",
    [int]$TimeoutSeconds = 600
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptRoot "..")

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $repoRoot "agent_outputs"
}

$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path $OutputRoot ("stress_" + $ts)
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$tasks = @(
  @{ agent = "orchestrator"; file = "orchestrator_plan.md"; message = "Create a 1-week execution plan for a multi-agent crawl + ledger classifier pipeline. Include milestones, dependencies, and owner roles. Output markdown with headings and bullets." },
  @{ agent = "research"; file = "ledger_rules_construction.md"; message = "Provide 12 ledger rule patterns for construction vendors or memos. Output a markdown table with pattern, category, confidence, review (true/false)." },
  @{ agent = "coder"; file = "ingest_crawl_improvements.md"; message = "Propose improvements to ingest_financials.py and the repo crawler/index. Focus on schema, parsing, and performance. Output bullets plus any suggested schema fields." },
  @{ agent = "qa"; file = "pipeline_qa_checklist.md"; message = "Create a QA checklist for the ingestion + classification pipeline (CSV ingest, rules, review queue). Output markdown checklist." },
  @{ agent = "release"; file = "guardrails_rollback.md"; message = "Draft guardrails for external actions (email, posting, payments) plus a rollback plan. Keep it concise and actionable." },
  @{ agent = "analyst"; file = "ops_metrics.md"; message = "Define system health metrics and alert thresholds for multi-agent ops (latency, error rate, queue depth, cost, approvals). Output bullets." },
  @{ agent = "finance"; file = "cash_flow_phase_map.md"; message = "Map construction cash-flow cycles by phase (precon, foundation, framing, windows, MEP, drywall, finishes). List inflows and outflows per phase." },
  @{ agent = "scout"; file = "payroll_improvements.md"; message = "List 5 high-impact improvement ideas for a payroll app focused on data integrity, reporting, and auditability. Output short bullets." }
)

$jobs = foreach ($t in $tasks) {
  $outfile = Join-Path $outDir $t.file
  Start-Job -ArgumentList $t.agent, $t.message, $outfile -ScriptBlock {
    param($agent, $msg, $outfile)
    $result = openclaw agent --agent $agent --message $msg --thinking low
    $result | Out-File -FilePath $outfile -Encoding utf8
  }
}

$jobs | Wait-Job -Timeout $TimeoutSeconds | Out-Null
$jobs | Receive-Job | Out-Null

Write-Output "Stress test outputs written to $outDir"
