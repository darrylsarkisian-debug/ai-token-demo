<#
.SYNOPSIS
  One-click entry point for the live demo: generates pseudo Copilot usage
  data, builds the dashboard, and opens it in the default browser.
#>

$scriptDir = $PSScriptRoot

& "$scriptDir\Generate-PseudoUsage.ps1"
Write-Host ""
& "$scriptDir\Build-Dashboard.ps1"
Write-Host ""
Write-Host "Opening dashboard..." -ForegroundColor Cyan
Start-Process "$scriptDir\dashboard.html"
