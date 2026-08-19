<#
.SYNOPSIS
  DEMO MODE collector: simulates resolving each user's department via Entra ID
  and pulling a Microsoft 365 Copilot usage report, then writes usage_data.json.

.NOTES
  What this stands in for in production:
   - Department resolution:
       Invoke-MgGraphRequest -Method GET -Uri "https://graph.microsoft.com/v1.0/users/<id>/memberOf"
       (or a maintained group -> department mapping table)
   - Usage pull:
       Invoke-MgGraphRequest -Method GET `
         -Uri "https://graph.microsoft.com/v1.0/reports/getCopilotUsageUserDetail(period='D30')"
     This requires Reports.Read.All admin consent and an M365 Copilot license
     on the tenant, which is not wired up for this demo.

  Token/cost figures below are MODELED, not returned by Graph. Microsoft's
  Copilot usage report gives interaction/activity counts per app, not raw
  token counts. This script applies a documented per-interaction token
  multiplier ($tokensPerInteraction) so the rest of the pipeline (dashboard,
  ERP export) can be demonstrated end to end with realistic-looking numbers.
#>

param(
    [string]$OutputPath = "$PSScriptRoot\usage_data.json"
)

Write-Host "=== AI Token Usage Collector (DEMO MODE) ===" -ForegroundColor Cyan
Write-Host ""

$departments = [ordered]@{
    "Finance" = @("avery.chen","jordan.patel","morgan.diaz","riley.osei","sam.novak","taylor.reyes","casey.lindqvist")
    "Sales"   = @("drew.kowalski","jamie.oduya","logan.ferreira","parker.singh","quinn.almeida","reese.tanaka","skyler.bianchi","emerson.villareal","harper.souza")
}

$apps = @("Copilot Chat","Word","Excel","PowerPoint","Outlook","Teams")
$tokensPerInteraction = 750
$costPer1kTokens = 0.02

Write-Host "Step 1: Resolving department membership via Entra ID (Microsoft Graph)..." -ForegroundColor Yellow
foreach ($dept in $departments.Keys) {
    foreach ($user in $departments[$dept]) {
        Write-Host ("  {0,-28} -> {1}" -f "$user@contoso.com", $dept)
    }
}
Write-Host ""

Write-Host "Step 2: Requesting Copilot usage report (Graph: reports/getCopilotUsageUserDetail)..." -ForegroundColor Yellow
Write-Host "  Report period: last 30 days"
Write-Host ""

$today = Get-Date
$events = @()

for ($d = 29; $d -ge 0; $d--) {
    $day = $today.AddDays(-$d)
    if ($day.DayOfWeek -eq [System.DayOfWeek]::Saturday -or $day.DayOfWeek -eq [System.DayOfWeek]::Sunday) { continue }

    foreach ($dept in $departments.Keys) {
        foreach ($user in $departments[$dept]) {
            if ((Get-Random -Minimum 0 -Maximum 100) -gt 55) { continue }
            $nApps = Get-Random -Minimum 1 -Maximum 4
            $chosenApps = $apps | Get-Random -Count $nApps
            foreach ($app in $chosenApps) {
                $interactions = Get-Random -Minimum 1 -Maximum 15
                $tokens = ($interactions * $tokensPerInteraction) + (Get-Random -Minimum -100 -Maximum 150)
                if ($tokens -lt 50) { $tokens = 50 }
                $cost = [Math]::Round(($tokens / 1000) * $costPer1kTokens, 4)
                $events += [PSCustomObject]@{
                    date         = $day.ToString("yyyy-MM-dd")
                    department   = $dept
                    user         = "$user@contoso.com"
                    app          = $app
                    interactions = $interactions
                    tokens       = $tokens
                    cost_usd     = $cost
                }
            }
        }
    }
}

$events | ConvertTo-Json -Depth 5 | Set-Content -Path $OutputPath -Encoding UTF8

Write-Host ("Captured {0} usage events across {1} departments." -f $events.Count, $departments.Keys.Count) -ForegroundColor Green
Write-Host "Written to: $OutputPath"
