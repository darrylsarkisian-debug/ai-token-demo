"""Live Microsoft 365 Copilot usage via Microsoft Graph.

IMPORTANT -- read before wiring this to a real tenant:

1. Auth: uses MSAL's interactive (delegated) flow, which pops a system
   browser for the signed-in user to authenticate. This still requires an
   Entra ID app registration (public client). DEFAULT_CLIENT_ID below is
   Microsoft's own "Microsoft Graph PowerShell" first-party client ID,
   which many tenants already have pre-consented for common delegated Graph
   scopes -- the same trick `Connect-MgGraph` uses under the hood. If your
   tenant blocks unregistered/first-party public clients, register your own
   app (public client, no secret needed for the interactive flow) and pass
   its Client ID in instead.

2. Required delegated permission: Reports.Read.All (admin consent), plus
   User.Read.All to resolve each user's `department` attribute.

3. Data shape: as of the version documented at build time, the v1
   getMicrosoft365CopilotUsageUserDetail report gives a LAST ACTIVITY DATE
   per app per user for the report period -- not an interaction count and
   not a token count. This module reads that report and produces one
   pseudo-event per (user, app) pair with interactions=1 as a placeholder
   count, then applies the SAME documented token multiplier used in demo
   mode so the two modes are visually comparable. That estimate is flagged
   via the `tokensEstimated` field the caller returns -- never presented as
   a measured value.

   The v2 report reportedly exposes richer metrics than v1. This has not
   been validated against a live tenant -- when you have real Graph access,
   check the actual v2 response shape and tighten this up; the field names
   below (APP_ACTIVITY_FIELDS) may need adjusting.

This file has not been tested against a live Microsoft 365 tenant (this
environment has no tenant credentials). Treat it as a best-effort
implementation of the documented API, not a verified integration.
"""
import msal
import requests

GRAPH_SCOPES = ["Reports.Read.All", "User.Read.All"]
DEFAULT_CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"  # Microsoft Graph PowerShell

TOKENS_PER_INTERACTION = 750
COST_PER_1K_TOKENS = 0.02

APP_ACTIVITY_FIELDS = {
    "Copilot Chat": "copilotChatLastActivityDate",
    "Teams": "microsoftTeamsCopilotLastActivityDate",
    "Word": "wordCopilotLastActivityDate",
    "Excel": "excelCopilotLastActivityDate",
    "PowerPoint": "powerPointCopilotLastActivityDate",
    "Outlook": "outlookCopilotLastActivityDate",
}


class GraphAuthError(RuntimeError):
    pass


def acquire_token(tenant_id: str, client_id: str = DEFAULT_CLIENT_ID) -> str:
    app = msal.PublicClientApplication(
        client_id, authority=f"https://login.microsoftonline.com/{tenant_id}"
    )
    result = app.acquire_token_interactive(scopes=GRAPH_SCOPES)
    if "access_token" not in result:
        raise GraphAuthError(result.get("error_description", "Sign-in failed"))
    return result["access_token"]


def _resolve_department(upn: str, headers: dict, cache: dict) -> str | None:
    if upn in cache:
        return cache[upn]
    resp = requests.get(
        f"https://graph.microsoft.com/v1.0/users/{upn}?$select=department",
        headers=headers, timeout=15,
    )
    dept = resp.json().get("department") if resp.ok else None
    cache[upn] = dept
    return dept


def fetch_copilot_usage(tenant_id: str, client_id: str = DEFAULT_CLIENT_ID, period: str = "D28"):
    """Returns (events, warnings). Raises GraphAuthError on sign-in failure."""
    token = acquire_token(tenant_id, client_id)
    headers = {"Authorization": f"Bearer {token}"}
    warnings = []

    resp = requests.get(
        f"https://graph.microsoft.com/v1.0/reports/getMicrosoft365CopilotUsageUserDetail(period='{period}')"
        f"?$format=application/json",
        headers=headers, timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"Graph usage report request failed: {resp.status_code} {resp.text[:300]}")

    rows = resp.json().get("value", [])
    dept_cache: dict = {}
    events = []
    for row in rows:
        upn = row.get("userPrincipalName")
        if not upn:
            continue
        dept = _resolve_department(upn, headers, dept_cache) or "Unassigned"
        report_date = row.get("reportRefreshDate")
        for app_name, field in APP_ACTIVITY_FIELDS.items():
            if row.get(field):
                interactions = 1  # placeholder: v1 report gives a date, not a count -- see module docstring
                tokens = interactions * TOKENS_PER_INTERACTION
                cost = round(tokens / 1000 * COST_PER_1K_TOKENS, 4)
                events.append({
                    "date": report_date,
                    "department": dept,
                    "user": upn,
                    "app": app_name,
                    "interactions": interactions,
                    "tokens": tokens,
                    "cost_usd": cost,
                })

    if not events:
        warnings.append(
            "No Copilot activity returned for this tenant/period. This could mean no licensed "
            "users were active, or the account used to sign in lacks Reports.Read.All."
        )
    return events, warnings
