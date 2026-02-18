param(
    [string]$InputPath = "C:\Users\natha\Downloads\Actions.xlsx",
    [string]$DbPath = "",
    [string]$SheetName = "All Tasks",
    [string]$TempCsv = ""
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $DbPath) {
    $DbPath = Join-Path $scriptRoot "..\data\actions.sqlite"
}

if (-not $TempCsv) {
    $TempCsv = Join-Path $env:TEMP ("actions_writeback_{0}.csv" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $pythonCmd) {
    throw "Python not found. Install Python 3 and ensure it is on PATH."
}

$exportScript = Join-Path $scriptRoot "actions_export_db.py"
& $pythonCmd.Source $exportScript --db $DbPath --out $TempCsv
if ($LASTEXITCODE -ne 0) {
    throw "Export failed. See output above."
}

$rows = @(Import-Csv -Path $TempCsv)

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $wb = $excel.Workbooks.Open($InputPath)
    $ws = $null
    foreach ($sheet in $wb.Worksheets) {
        if ($sheet.Name -eq $SheetName) { $ws = $sheet; break }
    }
    if (-not $ws) {
        $ws = $wb.Worksheets.Add()
        $ws.Name = $SheetName
    }

    $ws.Cells.Clear()
    $headers = @("Title","Tags","Status","Due Date","Priority","Next Action","Notes","Source")
    $ws.Range("A1").Resize(1, $headers.Count).Value2 = $headers

    if ($rows.Count -gt 0) {
        $data = New-Object 'object[,]' $rows.Count, $headers.Count
        for ($i=0; $i -lt $rows.Count; $i++) {
            $row = $rows[$i]
            $data[$i, 0] = $row.Title
            $data[$i, 1] = $row.Tags
            $data[$i, 2] = $row.Status
            $data[$i, 3] = $row.'Due Date'
            $data[$i, 4] = $row.Priority
            $data[$i, 5] = $row.'Next Action'
            $data[$i, 6] = $row.Notes
            $data[$i, 7] = $row.Source
        }
        $ws.Range("A2").Resize($rows.Count, $headers.Count).Value2 = $data
    }

    $wb.Save()
    $wb.Close($true)
} finally {
    $excel.Quit()
    if ($wb) { [System.Runtime.Interopservices.Marshal]::ReleaseComObject($wb) | Out-Null }
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
    if (Test-Path $TempCsv) { Remove-Item $TempCsv -Force }
}

Write-Output "Synced $($rows.Count) tasks to '$SheetName' in $InputPath"
