"""Demo-mode data generator.

Stands in for a live Microsoft 365 Copilot usage pull. See graph_client.py
for the live equivalent, and README-APP.md for the documented assumptions
behind the token/cost multiplier used here.
"""
import random
from datetime import date, timedelta

DEPARTMENTS = {
    "Finance": ["avery.chen", "jordan.patel", "morgan.diaz", "riley.osei", "sam.novak", "taylor.reyes", "casey.lindqvist"],
    "Sales": ["drew.kowalski", "jamie.oduya", "logan.ferreira", "parker.singh", "quinn.almeida", "reese.tanaka", "skyler.bianchi", "emerson.villareal", "harper.souza"],
}
APPS = ["Copilot Chat", "Word", "Excel", "PowerPoint", "Outlook", "Teams"]
TOKENS_PER_INTERACTION = 750
COST_PER_1K_TOKENS = 0.02


def generate_events(days: int = 30, domain: str = "contoso.com"):
    today = date.today()
    start = today - timedelta(days=days - 1)
    events = []
    for dept, users in DEPARTMENTS.items():
        for u in users:
            lo, hi = max(1, days // 3), max(2, days * 2 // 3)
            active_days = random.sample(range(days), k=random.randint(lo, hi))
            for d in active_days:
                day = start + timedelta(days=d)
                if day.weekday() >= 5:
                    continue
                n_apps = random.randint(1, 3)
                for app in random.sample(APPS, n_apps):
                    interactions = random.randint(1, 14)
                    tokens = max(50, interactions * TOKENS_PER_INTERACTION + random.randint(-100, 150))
                    cost = round(tokens / 1000 * COST_PER_1K_TOKENS, 4)
                    events.append({
                        "date": day.isoformat(),
                        "department": dept,
                        "user": f"{u}@{domain}",
                        "app": app,
                        "interactions": interactions,
                        "tokens": tokens,
                        "cost_usd": cost,
                    })
    return events
