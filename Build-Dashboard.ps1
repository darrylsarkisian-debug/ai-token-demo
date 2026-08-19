<#
.SYNOPSIS
  Aggregates usage_data.json by department/day/app/user and injects it into
  dashboard_template.html to produce a self-contained dashboard.html
  (no server, no external network calls — safe to open directly in a browser).
#>

param(
    [string]$DataPath     = "$PSScriptRoot\usage_data.json",
    [string]$TemplatePath = "$PSScriptRoot\dashboard_template.html",
    [string]$OutputPath   = "$PSScriptRoot\dashboard.html"
)

Write-Host "=== Building department usage dashboard ===" -ForegroundColor Cyan

if (-not (Test-Path $DataPath)) {
    Write-Host "No usage_data.json found. Run Generate-PseudoUsage.ps1 first." -ForegroundColor Red
    exit 1
}

$events = Get-Content -Path $DataPath -Raw -Encoding UTF8 | ConvertFrom-Json
$departments = $events | Select-Object -ExpandProperty department -Unique

$totalTokens = ($events | Measure-Object -Property tokens -Sum).Sum
$totalCost   = [Math]::Round(($events | Measure-Object -Property cost_usd -Sum).Sum, 2)
$activeUsers = ($events | Select-Object -ExpandProperty user -Unique).Count

$deptSummary = foreach ($dept in $departments) {
    $deptEvents = $events | Where-Object { $_.department -eq $dept }
    $deptTokens = ($deptEvents | Measure-Object -Property tokens -Sum).Sum
    $deptCost   = [Math]::Round(($deptEvents | Measure-Object -Property cost_usd -Sum).Sum, 2)
    $deptUsers  = ($deptEvents | Select-Object -ExpandProperty user -Unique).Count
    [PSCustomObject]@{
        name           = $dept
        tokens         = $deptTokens
        cost           = $deptCost
        users          = $deptUsers
        avgCostPerUser = [Math]::Round($deptCost / [Math]::Max($deptUsers, 1), 2)
    }
}

$dates = $events | Select-Object -ExpandProperty date -Unique | Sort-Object
$dailyTrend = foreach ($d in $dates) {
    $row = [ordered]@{ date = $d }
    foreach ($dept in $departments) {
        $sum = ($events | Where-Object { $_.date -eq $d -and $_.department -eq $dept } | Measure-Object -Property tokens -Sum).Sum
        if (-not $sum) { $sum = 0 }
        $row[$dept] = $sum
    }
    [PSCustomObject]$row
}

$topUsers = $events | Group-Object -Property user | ForEach-Object {
    [PSCustomObject]@{
        user       = $_.Name
        department = $_.Group[0].department
        tokens     = ($_.Group | Measure-Object -Property tokens -Sum).Sum
        cost       = [Math]::Round(($_.Group | Measure-Object -Property cost_usd -Sum).Sum, 2)
    }
} | Sort-Object -Property tokens -Descending | Select-Object -First 10

$byApp = $events | Group-Object -Property app | ForEach-Object {
    [PSCustomObject]@{
        app    = $_.Name
        tokens = ($_.Group | Measure-Object -Property tokens -Sum).Sum
        cost   = [Math]::Round(($_.Group | Measure-Object -Property cost_usd -Sum).Sum, 2)
    }
} | Sort-Object -Property tokens -Descending

$payload = [ordered]@{
    generatedAt = (Get-Date).ToString("yyyy-MM-dd HH:mm")
    demoMode    = $true
    kpis        = [ordered]@{
        totalTokens     = $totalTokens
        totalCost       = $totalCost
        departmentCount = @($departments).Count
        activeUsers     = $activeUsers
    }
    departments = @($deptSummary)
    dailyTrend  = @($dailyTrend)
    topUsers    = @($topUsers)
    byApp       = @($byApp)
}

$json = $payload | ConvertTo-Json -Depth 10 -Compress

$template = Get-Content -Path $TemplatePath -Raw -Encoding UTF8
$final = $template.Replace("__USAGE_DATA_JSON__", $json)
Set-Content -Path $OutputPath -Value $final -Encoding UTF8

Write-Host "Dashboard written to: $OutputPath" -ForegroundColor Green
