<#
.SYNOPSIS
  Initializes git in this project, commits everything, creates a GitHub repo
  under darrylsarkisian-debug, and pushes.

.NOTES
  Run this from a normal PowerShell window with this project folder as the
  working directory (or just run the script -- it doesn't depend on cwd
  beyond needing to be located in the project root).

  Requires: git (https://git-scm.com/download/win)
  Optional but recommended: GitHub CLI (winget install --id GitHub.cli),
  authenticated via `gh auth login`. Without it, the script falls back to
  printing manual steps.

.PARAMETER RepoName
  Name of the GitHub repo to create. Defaults to "ai-token-demo".

.PARAMETER Private
  Create the repo as private instead of public.
#>

param(
    [string]$RepoName = "ai-token-demo",
    [string]$Owner = "darrylsarkisian-debug",
    [switch]$Private
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Clean up any partial/broken .git folder from a previous attempt (e.g. one
# created over a network/synced mount that couldn't clean up its own lock
# files properly).
if (Test-Path ".git") {
    Write-Host "Removing existing .git folder (previous attempt)..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force ".git"
}

Write-Host "Initializing git repo..." -ForegroundColor Cyan
git init | Out-Null
git config user.name "Darryl Sarkisian"
git config user.email "darrylsarkisian@gmail.com"

git add -A
git commit -m "Initial commit: AI token usage tracking demo + app"
git branch -M main

$ghAvailable = Get-Command gh -ErrorAction SilentlyContinue

if ($ghAvailable) {
    Write-Host "GitHub CLI found. Creating repo and pushing..." -ForegroundColor Cyan

    $ghAuthStatus = gh auth status 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "You're not signed in to GitHub CLI yet. Running 'gh auth login'..." -ForegroundColor Yellow
        gh auth login
    }

    $visibilityFlag = if ($Private) { "--private" } else { "--public" }
    gh repo create "$Owner/$RepoName" $visibilityFlag --source=. --remote=origin --push

    Write-Host ""
    Write-Host "Done. Repo: https://github.com/$Owner/$RepoName" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "GitHub CLI (gh) not found. Two options:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Option A -- install GitHub CLI and rerun this script:"
    Write-Host "    winget install --id GitHub.cli"
    Write-Host "    gh auth login"
    Write-Host "    .\Publish-ToGitHub.ps1"
    Write-Host ""
    Write-Host "  Option B -- do it manually:"
    Write-Host "    1. Go to https://github.com/new"
    Write-Host "    2. Owner: $Owner   Repository name: $RepoName"
    Write-Host "    3. Do NOT initialize with a README/.gitignore/license (this folder already has a commit)"
    Write-Host "    4. Click 'Create repository', then run:"
    Write-Host "         git remote add origin https://github.com/$Owner/$RepoName.git"
    Write-Host "         git push -u origin main"
}
