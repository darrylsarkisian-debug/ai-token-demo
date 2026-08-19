@echo off
REM Double-click this file to run the live demo.
REM Bypasses execution policy for this one run only — does not change any
REM system-wide PowerShell settings.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-LiveDemo.ps1"
echo.
echo Demo complete. Dashboard should have opened in your browser.
pause
