param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8090
)

$env:AGENT_OPS_HOST = $BindHost
$env:AGENT_OPS_PORT = $Port
python ..\webui\server.py
