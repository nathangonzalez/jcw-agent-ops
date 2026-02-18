param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8090
)

$env:AGENT_OPS_HOST = $Host
$env:AGENT_OPS_PORT = $Port
python webui\server.py
