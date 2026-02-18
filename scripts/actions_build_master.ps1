param(
    [string]$InputPath = "C:\Users\natha\Downloads\Actions.xlsx",
    [string]$OutputSheet = "All Tasks",
    [switch]$Overwrite
)

$tagMap = @{
    "Home" = "home"
    "JCW To Do" = "business,jcw"
    "JCW_To_Do" = "business,jcw"
    "JCW Research" = "research,jcw"
    "JCW_Research" = "research,jcw"
    "Reno 2.0 To Do" = "project:reno"
    "Reno_2_0_To_Do" = "project:reno"
    "JCW Closing Checklist" = "project:closing,jcw"
    "JCW_Closing_Checklist" = "project:closing,jcw"
    "JCW Closing Checklist(new)" = "project:closing,jcw"
    "JCW_Closing_Checklist_new_" = "project:closing,jcw"
    "Home Maintenance List" = "home,maintenance,recurring"
    "Home_Maintenance_List" = "home,maintenance,recurring"
}

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$wb = $excel.Workbooks.Open($InputPath)

function Normalize-Text($value) {
    if ($null -eq $value) { return "" }
    return ([string]$value).Trim().ToLower()
}

function Find-HeaderRow($vals, $colCount, $maxRows, $candidates) {
    for ($r=1; $r -le $maxRows; $r++) {
        for ($c=1; $c -le $colCount; $c++) {
            $cell = Normalize-Text $vals[$r, $c]
            if ($candidates -contains $cell) {
                return $r
            }
        }
    }
    return $null
}

function Get-HeaderIndex($vals, $headerRow, $colCount, $candidates) {
    for ($c=1; $c -le $colCount; $c++) {
        $cell = Normalize-Text $vals[$headerRow, $c]
        if ($candidates -contains $cell) { return $c }
    }
    return $null
}

# Create or get output sheet
$target = $null
foreach ($ws in $wb.Worksheets) {
    if ($ws.Name -eq $OutputSheet) { $target = $ws; break }
}
if (-not $target) {
    $target = $wb.Worksheets.Add()
    $target.Name = $OutputSheet
} elseif ($Overwrite) {
    $target.Cells.Clear()
}

$headers = @("Title","Tags","Status","Due Date","Priority","Next Action","Notes","Source")
$target.Range("A1").Resize(1, $headers.Count).Value2 = $headers

$rows = New-Object System.Collections.Generic.List[object[]]

foreach ($ws in $wb.Worksheets) {
    $sheetName = $ws.Name
    if ($sheetName -eq $OutputSheet) { continue }
    if (-not $tagMap.ContainsKey($sheetName)) { continue }

    $used = $ws.UsedRange
    $vals = $used.Value2
    if (-not $vals) { continue }

    if ($vals -isnot [object[,]]) {
        $vals = ,@($vals)
    }

    $rowCount = $vals.GetLength(0)
    $colCount = $vals.GetLength(1)
    if ($rowCount -lt 2) { continue }

    $headerRow = Find-HeaderRow $vals $colCount ([Math]::Min(5, $rowCount)) @("actions","task","item","seller interview questions")
    if (-not $headerRow) { continue }

    $titleIdx = Get-HeaderIndex $vals $headerRow $colCount @("actions","task","item","seller interview questions")
    $dueIdx = Get-HeaderIndex $vals $headerRow $colCount @("due date","next due")
    $statusIdx = Get-HeaderIndex $vals $headerRow $colCount @("status")
    $notesIdx = Get-HeaderIndex $vals $headerRow $colCount @("comments","notes")

    for ($r=$headerRow+1; $r -le $rowCount; $r++) {
        $title = if ($titleIdx) { $vals[$r, $titleIdx] } else { $null }
        if (-not $title) { continue }
        $titleStr = [string]$title
        if ($titleStr.Trim() -eq "") { continue }

        $due = if ($dueIdx) { $vals[$r, $dueIdx] } else { $null }
        $status = if ($statusIdx) { $vals[$r, $statusIdx] } else { $null }
        $notes = if ($notesIdx) { $vals[$r, $notesIdx] } else { $null }

        $tags = $tagMap[$sheetName]

        $rows.Add(@($titleStr.Trim(), $tags, $status, $due, "", "", $notes, $sheetName))
    }
}

if ($rows.Count -gt 0) {
    $data = New-Object 'object[,]' $rows.Count, $headers.Count
    for ($i=0; $i -lt $rows.Count; $i++) {
        for ($j=0; $j -lt $headers.Count; $j++) {
            $data[$i, $j] = $rows[$i][$j]
        }
    }
    $target.Range("A2").Resize($rows.Count, $headers.Count).Value2 = $data
}

$wb.Save()
$wb.Close($true)
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($wb) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()

Write-Output "Wrote $($rows.Count) tasks to '$OutputSheet' in $InputPath"
