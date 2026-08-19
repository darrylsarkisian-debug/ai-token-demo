<#
.SYNOPSIS
  Starts the Python backend by hand. Use this if the WPF app's automatic
  launch fails, or if you just want to watch the backend logs while testing.

.NOTES
  Requires Python 3.10+ on PATH with the packages in backend\requirements.txt
  installed. First time only:

      cd backend
      pip install -r requirements.txt
#>

$backendDir = Join-Path $PSScriptRoot "backend"
Set-Location $backendDir

Write-Host "Starting backend on http://127.0.0.1:8731 ..." -ForegroundColor Cyan
python -m uvicorn main:app --host 127.0.0.1 --port 8731
