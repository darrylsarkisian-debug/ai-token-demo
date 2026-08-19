"""Local history store.

This is the retention differentiator: Microsoft's native Copilot usage
report is capped at a 28-day rolling window. Every live pull made through
this app is appended here, so the app accumulates history for as long as
it's been run -- weeks or months -- independent of Microsoft's window.

Demo-mode pulls are NOT persisted (they're synthetic and would just pollute
the history with fake data on every refresh).
"""
import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usage_history.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usage_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pulled_at TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            date TEXT NOT NULL,
            department TEXT NOT NULL,
            user TEXT NOT NULL,
            app TEXT NOT NULL,
            interactions INTEGER,
            tokens INTEGER,
            cost_usd REAL,
            UNIQUE(tenant_id, date, user, app)
        )
    """)
    conn.commit()
    conn.close()


def save_events(events, tenant_id):
    conn = sqlite3.connect(DB_PATH)
    pulled_at = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        """INSERT OR REPLACE INTO usage_events
           (pulled_at, tenant_id, date, department, user, app, interactions, tokens, cost_usd)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        [(pulled_at, tenant_id, e["date"], e["department"], e["user"], e["app"],
          e.get("interactions"), e.get("tokens"), e.get("cost_usd")) for e in events],
    )
    conn.commit()
    conn.close()


def load_history(tenant_id, since_date=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    q = "SELECT date, department, user, app, interactions, tokens, cost_usd FROM usage_events WHERE tenant_id = ?"
    params = [tenant_id]
    if since_date:
        q += " AND date >= ?"
        params.append(since_date)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def history_span_days(tenant_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT MIN(date), MAX(date) FROM usage_events WHERE tenant_id = ?", (tenant_id,)
    ).fetchone()
    conn.close()
    if not row or not row[0]:
        return 0
    from datetime import date as d
    lo = d.fromisoformat(row[0])
    hi = d.fromisoformat(row[1])
    return (hi - lo).days + 1
