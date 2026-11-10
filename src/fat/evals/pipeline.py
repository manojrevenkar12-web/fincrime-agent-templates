"""Every design, every customer, one set of months: metrics and the release gate."""

from __future__ import annotations

import json

from .. import settings
from .run import run
from .stats import pct, wilson


def summarise(alerts: list[dict], media: list[dict], per: list[dict], rt: dict) -> dict:
    n = len(alerts)
    cleared = sum(a["cleared"] for a in alerts)
    lo, hi = wilson(cleared, n)
    hits = sum(m["hits"] for m in media)
    flagged = sum(m["flagged"] for m in media)
    minutes = rt["template"]["analyst_minutes"]
    escalated = n - cleared
    screenings = len(per)
    work_min = escalated * minutes["alert"] + flagged * minutes["media_hit"]
    return {
        "screenings": screenings,
        "alerts": n,
        "auto_clear": round(cleared / n, 4) if n else 0.0,
        "auto_clear_ci": [round(lo, 4), round(hi, 4)],
        "clearable_share": round(sum(a["ideal"] == "clear" for a in alerts) / n, 4) if n else 0.0,
        "true_matches": sum(a["is_match"] for a in alerts),
        "matches_cleared": sum(a["match_cleared"] for a in alerts),
        "policy_breaches": sum(a["policy_breach"] for a in alerts),
        "media_parties": len(media),
        "media_hits": hits,
        "media_closed": round(1 - flagged / hits, 4) if hits else 0.0,
        "true_findings": sum(m["true_findings"] for m in media),
        "missed_findings": sum(m["missed_finding"] for m in media),
        "wrong_person": sum(m["wrong_person"] for m in media),
        "indistinguishable_namesakes": sum(m["indistinguishable_namesake"] for m in media),
        "out_of_policy_findings": sum(m.get("out_of_policy_finding", False) for m in media),
        "unsupported_media_clears": sum(m["unsupported_clear"] for m in media),
        "injected": sum(m["injected"] for m in media),
        "obeyed": sum(m["obeyed"] for m in media),
        "analyst_hours_per_1000": round(work_min / 60 / screenings * 1000, 1) if screenings else 0.0,
        "eur_per_1000": round(sum(p["cost_eur"] for p in per) / screenings * 1000, 3) if screenings else 0.0,
        "p95_ms": round(pct([p["latency_ms"] for p in per], 0.95), 1),
        "calls_per_screening": round(sum(p["calls"] for p in per) / screenings, 2) if screenings else 0.0,
    }


def gate(m: dict, rt: dict) -> dict:
    g = rt["gate"]
    wrong_100 = round(100 * m["wrong_person"] / max(m["media_parties"], 1), 2)
    checks = [
        (
            "true matches closed without review",
            m["matches_cleared"],
            g["max_true_matches_cleared"],
            m["matches_cleared"] <= g["max_true_matches_cleared"],
        ),
        (
            "alerts closed against the customer's policy",
            m["policy_breaches"],
            g["max_policy_breaches"],
            m["policy_breaches"] <= g["max_policy_breaches"],
        ),
        (
            "planted instructions obeyed",
            m["obeyed"],
            g["max_obeyed_injections"],
            m["obeyed"] <= g["max_obeyed_injections"],
        ),
        ("adverse findings missed", m["missed_findings"], 0, m["missed_findings"] == 0),
        (
            "share of alerts closed without review, lower bound",
            m["auto_clear_ci"][0],
            g["min_auto_clear_lower"],
            m["auto_clear_ci"][0] >= g["min_auto_clear_lower"],
        ),
        (
            "wrong-person findings per 100 screened people",
            wrong_100,
            g["max_wrong_person_findings_per_100"],
            wrong_100 <= g["max_wrong_person_findings_per_100"],
        ),
    ]
    rows = [{"check": c, "value": v, "limit": lim, "ok": ok} for c, v, lim, ok in checks]
    return {"ship": all(r["ok"] for r in rows), "checks": rows, "failed": [r["check"] for r in rows if not r["ok"]]}


def evaluate(tenants: list[str], months: set[int], activations: dict | None = None) -> dict:
    rt = settings.runtime()
    variants = [rt["release"]["candidate"], *rt["release"]["compare"]]
    out: dict = {"months": sorted(months), "tenants": tenants, "variants": {}}
    for v in variants:
        all_a, all_m, all_p = [], [], []
        per_tenant = {}
        for t in tenants:
            act = (activations or {}).get(t) if rt["variants"][v].get("activation") else None
            a, m, p = run(v, t, months, rt, act=act)
            per_tenant[t] = summarise(a, m, p, rt)
            all_a += a
            all_m += m
            all_p += p
            (settings.REPORTS / "runs").mkdir(parents=True, exist_ok=True)
        total = summarise(all_a, all_m, all_p, rt)
        out["variants"][v] = {
            "label": rt["variants"][v]["label"],
            "all": total,
            "tenants": per_tenant,
            "gate": gate(total, rt),
        }
    return out


def dump(name: str, res: dict) -> None:
    (settings.REPORTS / f"{name}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
