# AI Token Usage Dashboard — desktop app (C# + Python)

A Windows desktop app: WPF (C#) front end, local Python (FastAPI) back end. Mode dropdown at the top switches between pseudo demo data and a live Microsoft 365 Copilot pull via Microsoft Graph.

This is a second, more ambitious build alongside the PowerShell/HTML demo in the parent folder (`..\Start-Demo.bat` etc.). **Keep that one as your guaranteed-working fallback for 8/24** — it's fully tested end to end. This app is new, has real value (a real installable app, live-data capability, a genuine differentiation story), but carries more first-run risk — see "What's tested vs. not" below before you rely on it live.

## What's in this folder

```
app/
  backend/                   Python FastAPI backend (fully tested in a sandboxed Linux env)
    main.py                  API: POST /api/usage {mode, tenantId, ...}
    pseudo_data.py           Demo-mode data generator
    aggregate.py             Shared aggregation logic (demo + live)
    graph_client.py          Live Microsoft Graph client (MSAL + Copilot usage report)
    store.py                 SQLite history store (the >28-day retention differentiator)
    requirements.txt
  frontend/
    AiTokenDashboard/        WPF (.NET 8) project — C# source, not yet compiled/tested
      AiTokenDashboard.csproj
      App.xaml / App.xaml.cs
      MainWindow.xaml / MainWindow.xaml.cs
      Models.cs
      BackendClient.cs
      BackendProcessManager.cs
  Start-Backend.ps1          Manual backend launcher (fallback if the app's auto-launch fails)
  README-APP.md              This file
```

## What's tested vs. not — read this first

**Backend: fully tested, right here, before you got it.** I ran it in a Linux sandbox — health check, demo-mode data generation and aggregation, and both live-mode error paths (missing tenant ID, unknown mode) all verified working with real HTTP requests. Demo mode will work exactly as shown.

**Live Microsoft Graph integration: written to the documented API, not tested against a live tenant.** I have no Microsoft 365 tenant credentials in this environment. The code in `graph_client.py` implements what Microsoft's docs describe for `getMicrosoft365CopilotUsageUserDetail` (v1), but:
- That report returns a **last-activity date per app**, not an interaction count or token count. The code turns "used app X in this period" into a single placeholder interaction, then applies the same modeled multiplier as demo mode — this is flagged in the UI (`tokensEstimated`), not presented as measured.
- Microsoft's newer v2 report reportedly exposes more — worth checking the real schema once you have tenant access and tightening `APP_ACTIVITY_FIELDS` accordingly.
- Interactive sign-in via MSAL still needs a public client ID. The default uses Microsoft's own "Microsoft Graph PowerShell" client ID, which is pre-consented for common scopes in many tenants (the same trick `Connect-MgGraph` relies on). If your tenant restricts that, register your own app (public client, no secret) and pass its Client ID into the app.
- Required permission: `Reports.Read.All` (admin consent) plus `User.Read.All` to resolve each user's `department` attribute.

**C# / WPF frontend: written, not compiled.** This sandbox has no .NET or Windows Desktop SDK available, so I could not build or run it. I wrote it deliberately conservative to minimize first-build risk: no third-party NuGet packages (only built-in WPF controls and `System.Text.Json`/`System.Net.Http.Json`), straightforward XAML, no exotic language features. But it has not been proven to compile. **Build it as your first step, today if possible, so there are days left to fix anything before 8/24** — not the night before.

## How to build and run

1. **Install prerequisites on the Windows machine:**
   - Python 3.10+ (for the backend)
   - .NET 8 SDK + Visual Studio 2022 (or `dotnet` CLI) with the ".NET desktop development" workload, for the WPF frontend

2. **Set up the backend:**
   ```powershell
   cd app\backend
   pip install -r requirements.txt
   ```
   Test it standalone first: `..\Start-Backend.ps1` from the `app` folder, then in another terminal:
   ```powershell
   curl http://127.0.0.1:8731/api/health
   ```
   You should get `{"status":"ok"}`.

3. **Build the frontend.** In Visual Studio: File → Open → Project/Solution → select `app\frontend\AiTokenDashboard\AiTokenDashboard.csproj` directly (no `.sln` is included — Visual Studio can open a `.csproj` on its own, or generate one with `dotnet new sln -n AiTokenDashboard` then `dotnet sln add AiTokenDashboard.csproj` from that folder). Build (Ctrl+Shift+B). Fix whatever the compiler flags — send me the errors and I'll patch the source.

4. **Copy the backend next to the built exe.** The app expects a `backend\` folder alongside `AiTokenDashboard.exe` (in `bin\Debug\net8.0-windows\` while developing). Copy `app\backend\` there, or just run the app from Visual Studio (F5) with `Start-Backend.ps1` already running in a separate terminal — either works.

5. **Run it.** Demo data should work immediately — select "Demo data," click "Load demo data." For live mode, select "Live Microsoft 365," enter your tenant ID or domain (e.g. `contoso.onmicrosoft.com`), click "Connect & pull live data" — a browser window should open for sign-in.

## The differentiator (why this app vs. Microsoft's own Copilot usage reports)

Researched directly against Microsoft's current documentation before writing any of this — here's the gap this app fills, stated plainly rather than oversold:

Microsoft's native Copilot usage reporting (admin center and the Graph API behind it) gives active users, prompts submitted, and last-activity-per-app dates. It does not give a token count, and it has no concept of dollar cost at all. It's also strictly per-user with no department or cost-center rollup — you'd have to build that mapping yourself even with their data. The reporting window is capped at 28 days, so there's no built-in historical trend beyond that. Coverage is limited to licensed Copilot users, so anyone using ChatGPT, Claude, or another AI tool outside Copilot is invisible in Microsoft's view. And there's no budget alerting or ERP export — it's a reporting surface, not a governance or finance tool.

This app's differentiators, concretely, in the code you now have:
- **Department rollup by default** (`aggregate.py`) — every view is department-first, not user-first.
- **Cost modeling** — a documented token/cost multiplier applied consistently, clearly flagged as an estimate rather than pretending to be billing-grade.
- **History beyond 28 days** (`store.py`) — every live pull is appended to a local SQLite database, so the app's own retention grows past whatever window Microsoft gives you.
- **A foundation for cross-vendor visibility** — the data model (department, user, app, tokens, cost) doesn't care whether the source is Copilot, ChatGPT, or a custom agent; adding another source later (per the original PRD) slots into the same schema.
- **A real exportable app**, not a report you have to log into the admin center to see.

What it does not yet do: ERP export (Dynamics 365, per the PRD) and budget alerts are not built — those are natural next additions on top of this data model.

## If something breaks before 8/24

- Backend won't start: run `Start-Backend.ps1` manually and read the console output — it'll say exactly what's missing (usually a `pip install`).
- WPF won't compile: send me the exact error text: I'll patch the source. Given I couldn't compile-check it myself, budget time for at least one round of this.
- Live Graph pull fails: check the `warnings`/`error` message the app shows — it's built to surface Microsoft's actual error text (permission denied, no licensed users, etc.) rather than fail silently.
- Anything not resolved in time: fall back to the PowerShell/HTML demo in the parent folder — it's fully tested and guaranteed to run.
