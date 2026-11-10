"""REST API: one endpoint per thing a customer integration or a case manager needs.

POST /v1/tenants/{tenant}/screenings   a screening from the customer's provider -> the agent's review
GET  /v1/tenants/{tenant}/queue        what analysts still have to decide, likely matches first
POST /v1/cases/{alert_id}/decision     an analyst's decision on an alert
GET  /v1/tenants/{tenant}/metrics      closed by the agent, sent to analysts, decided, open
"""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import settings
from .store import Store


class Alert(BaseModel):
    alert_id: str
    party_role: str
    party_name: str
    entry_id: str
    list: str
    matched_name: str
    score: float


class MediaHit(BaseModel):
    party_name: str
    article_id: str
    score: float


class Screening(BaseModel):
    screening_id: str
    screened_on: str
    record: dict
    alerts: list[Alert] = []
    media_hits: list[MediaHit] = []


class Decision(BaseModel):
    analyst: str
    decision: Literal["false_positive", "true_match"]
    note: str | None = None


def create_app(make_template, store: Store | None = None) -> FastAPI:
    """`make_template(tenant)` returns the activated template for a customer, or None if it is not live."""
    app = FastAPI(title="fincrime-agent-templates")
    db = store or Store()
    templates: dict = {}

    def template(tenant: str):
        if tenant not in templates:
            templates[tenant] = make_template(tenant)
        if templates[tenant] is None:
            raise HTTPException(404, f"no live activation for {tenant}")
        return templates[tenant]

    @app.post("/v1/tenants/{tenant}/screenings")
    def screen(tenant: str, s: Screening) -> dict:
        review = template(tenant).review(s.model_dump())
        db.save(tenant, s.screened_on, review)
        return {
            "screening_id": review.screening_id,
            "alerts": [
                {"alert_id": a.alert_id, "disposition": a.disposition, "reasons": a.reasons, "conflicts": a.conflicts}
                for a in review.alerts
            ],
            "media": [
                {"party": m.party_name, "disposition": m.disposition, "findings": m.findings, "unsure": m.unsure}
                for m in review.media
            ],
            "issues": review.issues,
            "flags": review.flags,
            "latency_ms": round(review.latency_ms, 1),
            "cost_eur": round(review.cost_eur, 6),
        }

    @app.get("/v1/tenants/{tenant}/queue")
    def queue(tenant: str) -> list[dict]:
        return db.queue(tenant)

    @app.post("/v1/cases/{alert_id}/decision")
    def decide(alert_id: str, d: Decision) -> dict:
        if not db.exists(alert_id):
            raise HTTPException(404, f"no alert {alert_id}")
        db.decide(alert_id, "alert", d.analyst, d.decision, d.note)
        return {"alert_id": alert_id, "decision": d.decision}

    @app.get("/v1/tenants/{tenant}/metrics")
    def metrics(tenant: str) -> dict:
        return db.metrics(tenant)

    return app


def demo_app() -> FastAPI:  # pragma: no cover - wiring for `uvicorn fat.api:demo_app --factory`
    from .evals.run import activation, make
    from .sim.model import build

    rt = settings.runtime()
    model, _ = build(rt, settings.DATA / "truth" / "world.json")

    def make_template(tenant: str):
        act = activation(tenant)
        return make("activated", tenant, model, rt, act=act) if act.get("live") else None

    return create_app(make_template)
