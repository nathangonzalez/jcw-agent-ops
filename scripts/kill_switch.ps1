param(
    [switch]$Hard,
    [string]$ConfigPath = "$env:USERPROFILE\.openclaw\openclaw.json"
)

$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Output "[$stamp] Kill switch engaged."

# Stop gateway
try { openclaw gateway stop | Out-Null } catch {}

if (Test-Path $ConfigPath) {
    try {
        $cfg = Get-Content -Raw -Path $ConfigPath | ConvertFrom-Json
        if ($cfg.tools -and $cfg.tools.web) {
            $cfg.tools.web.search.enabled = $false
            $cfg.tools.web.fetch.enabled = $false
        }
        if ($cfg.tools -and $cfg.tools.agentToAgent) {
            $cfg.tools.agentToAgent.enabled = $false
        }
        $cfg | ConvertTo-Json -Depth 20 | Set-Content -Path $ConfigPath -Encoding UTF8
    } catch {
        Write-Output "Failed to edit config: $ConfigPath"
    }
}

if ($Hard) {
    Write-Output "Hard mode: revoke keys manually (OpenAI/Anthropic/Google) and block outbound network if needed."
}

$logLine = "$stamp | KILL_SWITCH: gateway stop; web search disabled; a2a disabled; hard=$Hard"
$repoRoot = Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..")
Add-Content -Path (Join-Path $repoRoot "agent.persist") -Value $logLine

Write-Output "Kill switch complete."
