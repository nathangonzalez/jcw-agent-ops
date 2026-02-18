param(
    [ValidateSet("daily", "weekly")] [string]$Mode = "weekly",
    [string]$Topic = "agentic modeling and multi-agent systems",
    [string]$OutputPath = ""
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptRoot "..")

$digestsRoot = Join-Path $repoRoot "research\digests"
$dailyDir = Join-Path $digestsRoot "daily"
$weeklyDir = Join-Path $digestsRoot "weekly"
New-Item -ItemType Directory -Force -Path $dailyDir | Out-Null
New-Item -ItemType Directory -Force -Path $weeklyDir | Out-Null

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $date = Get-Date -Format "yyyy-MM-dd"
    if ($Mode -eq "daily") {
        $OutputPath = Join-Path $dailyDir ("$date.md")
    } else {
        $OutputPath = Join-Path $weeklyDir ("weekly-$date.md")
    }
}

if ($Mode -eq "daily") {
    $prompt = @"
You are the research agent. Produce a DAILY scan for: $Topic.
Use $research-sme for structure and source policy. Use $spike-generator for proposed spikes. Use $evidence-grader if sources conflict.
Requirements:
- Focus on items from the last 7 days.
- Use primary sources when possible (papers, official docs, author talks).
- Include sections: Papers, Podcasts, Videos, Wiki/Docs, Key Insights, Proposed Spikes.
- For each item: title, author/channel, date, one-paragraph summary, and why it matters.
- Proposed Spikes: 1 to 3 items using the Spike Template fields (goal, scope, sources, experiment).
- Return markdown only.
"@
} else {
    $prompt = @"
You are the research agent. Produce a WEEKLY digest on: $Topic.
Use $research-sme for structure and source policy. Use $spike-generator for proposed spikes. Use $evidence-grader if sources conflict.
Requirements:
- Use primary sources when possible (papers, official docs, author talks).
- Include sections: Papers, Podcasts, Videos, Wiki/Docs, Key Insights, Proposed Spikes.
- For each item: title, author/channel, date, one-paragraph summary, and why it matters.
- Proposed Spikes: 3 to 5 items using the Spike Template fields (goal, scope, sources, experiment).
- Return markdown only.
"@
}

$result = openclaw agent --agent research --message $prompt --thinking low
$result | Out-File -FilePath $OutputPath -Encoding utf8

# Append spikes to backlog if section exists
$backlogPath = Join-Path $repoRoot "research\RESEARCH_BACKLOG.md"
if (Test-Path $OutputPath) {
    $lines = Get-Content -Path $OutputPath
    $start = $lines | Select-String -Pattern '^## Proposed Spikes' | Select-Object -First 1
    if ($start) {
        $startIndex = $start.LineNumber - 1
        $endIndex = $lines.Length - 1
        for ($i = $startIndex + 1; $i -lt $lines.Length; $i++) {
            if ($lines[$i] -match '^## ') {
                $endIndex = $i - 1
                break
            }
        }
        if ($endIndex -gt $startIndex) {
            $stamp = Get-Date -Format "yyyy-MM-dd"
            Add-Content -Path $backlogPath -Value "`n---`n`n## Proposed Spikes ($Mode $stamp)`n"
            $lines[$startIndex..$endIndex] | Add-Content -Path $backlogPath
        }
    }
}

Write-Output "Wrote digest: $OutputPath"
