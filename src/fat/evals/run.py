"""Run one design for one customer over a set of months, scored against the truth."""

from __future__ import annotations

import json
from functools import cache

from .. import settings
from ..agent.evidence import Lists, Media
from ..agent.template import Template
from ..sim.model import build as build_sim
from .score import score_alert, score_media


@cache
def truth(tenant: str) -> dict:
    t = json.loads((settings.DATA / "truth" / f"{tenant}.json").read_text(encoding="utf-8"))
    return {"policy": t["policy"], "rows": {r["screening_id"]: r for r in t["rows"]}}


@cache
def world_truth() -> dict:
    return json.loads((settings.DATA / "truth" / "world.json").read_text(encoding="utf-8"))


@cache
def published() -> dict:
    with open(settings.DATA / "media" / "articles.jsonl", encoding="utf-8") as fh:
        return {a["id"]: a["published"] for a in map(json.loads, fh)}


def screenings(tenant: str) -> list[dict]:
    with open(settings.DATA / "tenants" / tenant / "screenings.jsonl", encoding="utf-8") as fh:
        return [json.loads(x) for x in fh]


def routing() -> dict:
    p = settings.CONFIG / "routing.json"
    return json.loads(p.read_text())["routing"] if p.exists() else {"remarks": "medium", "media": "medium"}


def activation(tenant: str) -> dict:
    p = settings.CONFIG / "activations" / f"{tenant}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def make(variant: str, tenant: str, model, rt: dict, act: dict | None = None, route: dict | None = None) -> Template:
    v = rt["variants"][variant]
    cust = settings.customer("_generic" if v.get("config") == "generic" else tenant)
    act = act if act is not None else (activation(tenant) if v.get("activation") else {})
    return Template(
        rt,
        cust,
        act,
        model,
        Lists(settings.ROOT / rt["paths"]["lists"]),
        Media(settings.ROOT / rt["paths"]["media"]),
        route or routing(),
        use_model=v.get("model", True),
        guards=v.get("guards", True),
    )


def run(
    variant: str,
    tenant: str,
    months: set[int],
    rt: dict | None = None,
    act: dict | None = None,
    route: dict | None = None,
) -> tuple[list[dict], list[dict], list[dict]]:
    rt = rt or settings.runtime()
    model, _ = build_sim(rt, settings.DATA / "truth" / "world.json")
    v = rt["variants"][variant]
    tpl = None if not v.get("automate", True) else make(variant, tenant, model, rt, act, route)
    tr = truth(tenant)
    arts = world_truth()["articles"]
    ctx = {
        "subjects": world_truth()["subjects"],
        "published": published(),
        "has_city": tenant in ("finvia", "northbank"),
    }
    alerts, media, per_screening = [], [], []
    for s in screenings(tenant):
        if s["month"] not in months:
            continue
        row = tr["rows"][s["screening_id"]]
        at = {a["alert_id"]: a for a in row["alerts"]}
        mt = {m["party_name"]: m for m in row["media"]}
        if tpl is None:
            for a in s["alerts"]:
                alerts.append(
                    {
                        "tenant": tenant,
                        "month": s["month"],
                        **score_alert("escalate", at[a["alert_id"]]),
                        "alert_id": a["alert_id"],
                        "list": a["list"],
                    }
                )
            hits: dict[str, list] = {}
            for h in s.get("media_hits", []):
                hits.setdefault(h["party_name"], []).append(h["article_id"])
            for name, ids in hits.items():
                media.append(
                    {"tenant": tenant, "month": s["month"], **score_media("escalate", [], ids, mt.get(name), arts, row)}
                )
            per_screening.append({"latency_ms": 0.0, "cost_eur": 0.0, "calls": 0})
            continue
        rv = tpl.review(s)
        for r in rv.alerts:
            alerts.append(
                {
                    "tenant": tenant,
                    "month": s["month"],
                    **score_alert(r.disposition, at[r.alert_id]),
                    "alert_id": r.alert_id,
                    "list": r.list,
                    "conflicts": [c["type"] + ":" + c["source"] for c in r.conflicts],
                }
            )
        for m in rv.media:
            flagged = [x["article"] for x in m.articles if x["verdict"] != "clear"]
            media.append(
                {
                    "tenant": tenant,
                    "month": s["month"],
                    **score_media(
                        m.disposition,
                        m.findings,
                        flagged,
                        mt.get(m.party_name),
                        arts,
                        row,
                        all_ids=[x["article"] for x in m.articles],
                        ctx=ctx,
                    ),
                }
            )
        per_screening.append(
            {"latency_ms": rv.latency_ms, "cost_eur": rv.cost_eur, "calls": len(rv.calls), "flags": len(rv.flags)}
        )
    return alerts, media, per_screening
