param(
    [string]$OutputRoot = "",
    [int]$TimeoutSeconds = 900
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptRoot "..")

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $repoRoot "agent_outputs"
}

$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path $OutputRoot ("lanes_" + $ts)
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$tasks = @(
  @{ agent = "coder"; file = "lane_infra.md"; message = "Infra Lane: Draft a monorepo CI/CD plan for App Engine services with patch deploy + promote. Include path filters, matrix strategy, and a minimal YAML outline. Focus on payroll, estimating, financials, suite-shell. Output concise markdown." },
  @{ agent = "analyst"; file = "lane_product.md"; message = "Product Lane: Define suite-shell UX for a single UI with app buttons. Provide nav structure, modules list, and routing options. Output concise markdown." },
  @{ agent = "finance"; file = "lane_finance.md"; message = "Finance Lane: Draft ledger taxonomy v1 + manual review triggers + cash flow phase mapping. Output headings and bullets." },
  @{ agent = "scout"; file = "lane_scout.md"; message = "Scout Lane: Create repo inventory template and populate any entries you can from local context. Include stack, deploy method, datastore, owners, risks. Output markdown table." },
  @{ agent = "research"; file = "lane_research.md"; message = "Research Lane: Build a short backlog of 5 agentic modeling spikes (papers/podcasts/tools). Include goal, hypothesis, evaluation, and minimal source list. Output concise markdown." }
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

Write-Output "Lane outputs written to $outDir"
