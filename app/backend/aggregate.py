"""Aggregation layer shared by demo and live modes.

Turns a flat list of usage events (date, department, user, app,
interactions, tokens, cost_usd) into the KPI/summary shapes the frontend
renders. tokens/cost_usd may be None for live events where Microsoft's
report doesn't provide a count (see graph_client.py) -- this module treats
None as 0 for aggregation but callers should check estimated_fields to know
whether figures are measured or modeled.
"""
from collections import defaultdict


def _num(v):
    return v if v is not None else 0


def aggregate(events, estimated: bool):
    departments = sorted(set(e["department"] for e in events)) or ["(none)"]
    dept_summary = []
    for dept in departments:
        de = [e for e in events if e["department"] == dept]
        tokens = sum(_num(e["tokens"]) for e in de)
        cost = round(sum(_num(e["cost_usd"]) for e in de), 2)
        users = len(set(e["user"] for e in de))
        dept_summary.append({
            "name": dept,
            "tokens": tokens,
            "cost": cost,
            "users": users,
            "avgCostPerUser": round(cost / max(users, 1), 2),
        })

    dates = sorted(set(e["date"] for e in events))
    daily_trend = []
    for d in dates:
        row = {"date": d}
        for dept in departments:
            row[dept] = sum(_num(e["tokens"]) for e in events if e["date"] == d and e["department"] == dept)
        daily_trend.append(row)

    user_agg = defaultdict(lambda: {"tokens": 0, "cost": 0.0, "department": None})
    for e in events:
        a = user_agg[e["user"]]
        a["tokens"] += _num(e["tokens"])
        a["cost"] += _num(e["cost_usd"])
        a["department"] = e["department"]
    top_users = sorted(
        [{"user": u, "department": v["department"], "tokens": v["tokens"], "cost": round(v["cost"], 2)}
         for u, v in user_agg.items()],
        key=lambda x: -x["tokens"],
    )[:10]

    app_agg = defaultdict(lambda: {"tokens": 0, "cost": 0.0})
    for e in events:
        app_agg[e["app"]]["tokens"] += _num(e["tokens"])
        app_agg[e["app"]]["cost"] += _num(e["cost_usd"])
    by_app = sorted(
        [{"app": a, "tokens": v["tokens"], "cost": round(v["cost"], 2)} for a, v in app_agg.items()],
        key=lambda x: -x["tokens"],
    )

    return {
        "kpis": {
            "totalTokens": sum(_num(e["tokens"]) for e in events),
            "totalCost": round(sum(_num(e["cost_usd"]) for e in events), 2),
            "departmentCount": len(departments),
            "activeUsers": len(set(e["user"] for e in events)),
        },
        "departments": dept_summary,
        "dailyTrend": daily_trend,
        "topUsers": top_users,
        "byApp": by_app,
        "tokensEstimated": estimated,
    }
