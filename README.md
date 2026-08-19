# AI token usage by department — live demo (Windows)

Scope: Microsoft 365 Copilot usage, 1–2 departments, IT leadership audience, cost/chargeback focus. Target date: 2026-08-24.

## What's in this folder

- `Start-Demo.bat` — double-click this to run the whole thing. Nothing else to install.
- `Run-LiveDemo.ps1` — orchestrates the two steps below and opens the dashboard.
- `Generate-PseudoUsage.ps1` — simulates department resolution + a Copilot usage pull, writes `usage_data.json`.
- `Build-Dashboard.ps1` — aggregates the data and builds `dashboard.html`.
- `dashboard_template.html` — the dashboard shell (used by the build step).
- `dashboard-preview.html` — a **pre-built fallback**. If PowerShell can't run live for any reason, open this file directly — same dashboard, already rendered, zero dependencies.

## How to run it live

1. Copy this whole folder onto the Windows machine you're presenting from.
2. Double-click `Start-Demo.bat`.
3. A console window opens and prints the simulated pipeline running — department resolution, then the usage report pull — then your browser opens with the dashboard.

That's it. No server, no ports, no internet connection required, no admin rights required. The `.bat` file bypasses PowerShell's execution policy for that one run only — it doesn't change any system settings.

If `Start-Demo.bat` doesn't work on the day (locked-down machine, execution policy blocked at the group-policy level, etc.), open `dashboard-preview.html` directly instead — it's the same dashboard already generated, and needs nothing but a browser.

## Suggested walkthrough

1. **Open the console, run `Start-Demo.bat`.** Narrate: "This is the collector that would run on each department's machines. Step one resolves the signed-in user's department from Entra ID; step two pulls their Copilot usage from Microsoft Graph."
2. **Dashboard opens.** Point to the KPI row — total tokens, total cost, departments tracked, active users, over the last 30 days.
3. **Cost by department bar chart** — this is the chargeback view: which department is generating the AI spend.
4. **Daily trend chart** — shows usage direction over time per department, useful for spotting spikes.
5. **Department summary table** — the number Finance would actually use: cost per department, average cost per user.
6. **Usage by app / top users tables** — drill-down for "who/what is driving this."
7. Close with the caveat below — this is exactly what earns credibility with an IT/Finance audience.

## What's real vs. simulated (say this out loud in the demo)

- **Simulated:** the department lookup (hardcoded mapping standing in for an Entra ID group query) and the Copilot usage pull (no tenant credentials wired up — needs `Reports.Read.All` admin consent and a Copilot license on the target tenant).
- **Modeled, not measured:** token and cost figures. Microsoft Graph's Copilot usage report (`getCopilotUsageUserDetail`) returns interaction/activity counts per app, not raw token counts. This demo applies a documented multiplier (750 tokens/interaction, $0.02/1K tokens) to turn that into token and cost figures. Getting real numbers means either pulling actual consumption data from the M365 admin center billing/metering side, or accepting interaction counts as the primary metric instead of tokens.
- **Everything else in the pipeline is real code that runs** — the department resolution step, the aggregation logic, and the dashboard are the actual shape of what production would do; only the two data sources are swapped for pseudo data.

## Path to production (per the PRD)

1. Swap `Generate-PseudoUsage.ps1`'s simulated steps for real calls: `Invoke-MgGraphRequest` against `reports/getCopilotUsageUserDetail` and a real Entra ID group/department lookup.
2. Decide on the token/cost model — real consumption data if your tenant exposes it, or keep interaction counts as the primary metric and drop the modeled multiplier.
3. Replace the local JSON file with the central ingestion service (FastAPI + Postgres) from the PRD so multiple machines can report in, not just one demo run.
4. Add the scheduled Dynamics 365 export (Dataverse Web API) once the target entity/module is decided.
5. Expand from 1–2 departments to the full pilot list once Entra ID group alignment is confirmed.

These map directly to the open questions in the PRD — worth resolving before Phase 2 starts.
