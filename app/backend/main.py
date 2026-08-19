"""Local backend for the AI Token Usage Dashboard.

Runs on 127.0.0.1 only -- this is a local sidecar process for the WPF
frontend, not a service meant to be exposed on the network.

Run it either way:

    uvicorn main:app --host 127.0.0.1 --port 8731

or just run/debug this file directly (F5 in VS Code, or `python main.py`) --
see the __main__ block at the bottom.
"""
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import pseudo_data
import aggregate
import store
import graph_client

app = FastAPI(title="AI Token Usage Dashboard Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

store.init_db()


class UsageRequest(BaseModel):
    mode: str  # "demo" | "live"
    tenantId: str | None = None
    clientId: str | None = None
    days: int = 30


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/usage")
def get_usage(req: UsageRequest):
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if req.mode == "demo":
        events = pseudo_data.generate_events(days=req.days)
        payload = aggregate.aggregate(events, estimated=True)
        payload["generatedAt"] = generated_at
        payload["source"] = "demo"
        payload["warnings"] = []
        payload["historyDays"] = req.days
        return payload

    if req.mode == "live":
        if not req.tenantId:
            return {"error": "tenantId is required for live mode"}
        try:
            client_id = req.clientId or graph_client.DEFAULT_CLIENT_ID
            events, warnings = graph_client.fetch_copilot_usage(req.tenantId, client_id)
        except graph_client.GraphAuthError as e:
            return {"error": f"Sign-in failed: {e}"}
        except Exception as e:
            return {"error": f"Live data pull failed: {e}"}

        store.save_events(events, req.tenantId)
        history = store.load_history(req.tenantId)
        payload = aggregate.aggregate(history, estimated=True)
        payload["generatedAt"] = generated_at
        payload["source"] = "live"
        payload["warnings"] = warnings
        payload["historyDays"] = store.history_span_days(req.tenantId)
        return payload

    return {"error": f"Unknown mode: {req.mode}"}


if __name__ == "__main__":
    # Lets you just run/debug this file directly (F5 in VS Code, or
    # `python main.py`) instead of needing the separate `uvicorn` command.
    # reload=False on purpose -- the debugger doesn't play well with
    # uvicorn's auto-reload subprocess.
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8731, reload=False)
