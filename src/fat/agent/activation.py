"""Activating the template for a customer, from the customer's own history and nothing else.

1. Mapping check: every record of the history parses, and the date format is the only one the data allows.
2. Backtest: the template runs on months 1-5; each alert's conflict weight is kept, so every threshold on the
   grid can be read off one run.
3. Threshold: the lowest that clears no more analyst-confirmed matches than label noise explains (a share of
   the clears), each of them with a conflicting structured field, listed for the customer's compliance team
   to confirm; and whose clears agree with analysts at the required precision.
4. Shadow month: month 6 with the chosen threshold, compared with what analysts decided.
5. Gate: all of the above, or the customer is not switched on.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .mapping import Mapping
from .template import Template


@dataclass
class History:
    screenings: list[dict]
    decisions: dict[str, str]

    @classmethod
    def load(cls, tenant_dir: Path) -> History:
        with open(tenant_dir / "screenings.jsonl", encoding="utf-8") as fh:
            rows = [json.loads(x) for x in fh]
        with open(tenant_dir / "analyst_decisions.jsonl", encoding="utf-8") as fh:
            decisions = {d["id"]: d["decision"] for d in map(json.loads, fh)}
        return cls([r for r in rows if r["split"] == "history"], decisions)


def mapping_check(customer: dict, history: History, runtime: dict) -> dict:
    """Parse every record; for each date-of-birth value, list the formats it fits."""
    formats = runtime["activation"]["date_formats"]
    m = Mapping(customer, formats)
    parties = parsed_dobs = 0
    issues: Counter = Counter()
    fits: Counter = Counter()
    for s in history.screenings:
        p = m.parse(s["record"])
        for i in p.issues:
            issues[i.split(" for ")[0]] += 1
        for party in p.parties:
            if party.kind != "person":
                continue
            parties += 1
            parsed_dobs += party.dob is not None
        for raw in _raw_dobs(s["record"], customer):
            fits[tuple(f for f in formats if _fits(raw, f))] += 1
    allowed = set(formats)
    for combo in fits:
        allowed &= set(combo)
    configured = customer["mapping"].get("dob_format")
    # the format the parser actually uses for each value: the configured one, or the first that fits
    used = {configured} if configured else {combo[0] for combo in fits if combo}
    rate = parsed_dobs / parties if parties else 0.0
    ok = rate >= runtime["activation"]["min_parse_rate"] and len(allowed) == 1 and used == allowed
    return {
        "people": parties,
        "dob_parse_rate": round(rate, 4),
        "formats_the_data_allows": sorted(allowed),
        "formats_the_parser_uses": sorted(f for f in used if f),
        "issues": dict(issues),
        "ok": ok,
    }


def _raw_dobs(rec: dict, customer: dict) -> list[str]:
    m = customer["mapping"]
    if m.get("mode") == "auto":
        keys = ["birth_date", "date_of_birth", "dob", "birthdate", "geburtsdatum"]
        found = [str(rec[k]) for k in keys if k in rec]
        for lst in ("parties", "persons", "beteiligte"):
            for p in rec.get(lst, []) or []:
                found += [str(p[k]) for k in keys if k in p]
        return found
    path, field = m.get("person_path"), m.get("dob")
    people = rec.get(path, []) if path else [rec]
    return [str(p[field]) for p in people if p.get(field)]


def _fits(raw: str, fmt: str) -> bool:
    try:
        datetime.strptime(raw, fmt)
        return True
    except ValueError:
        return False


def disposition_at(r, theta: float, min_conflicts: int) -> str:
    if r.disposition == "likely_match":
        return "likely_match"
    kinds = {c["type"] for c in r.conflicts}
    return "clear" if len(kinds) >= min_conflicts and r.clear_score >= theta else "escalate"


def activate(customer: dict, runtime: dict, history: History, make_template) -> dict:
    a = runtime["activation"]
    report: dict = {"customer": customer["id"], "mapping": mapping_check(customer, history, runtime)}
    tpl: Template = make_template({"theta": 0.0})
    back = [s for s in history.screenings if s["month"] < a["shadow_month"]]
    shadow = [s for s in history.screenings if s["month"] == a["shadow_month"]]
    results = [r for s in back for r in tpl.review(s).alerts]
    confirmed = [r for r in results if history.decisions.get(r.alert_id) == "true_match"]
    grid = []
    chosen = None
    for theta in runtime["template"]["theta_grid"]:
        d = {r.alert_id: disposition_at(r, theta, customer["policy"]["min_conflicts"]) for r in results}
        cleared = [r for r in results if d[r.alert_id] == "clear"]
        cleared_matches = [r for r in cleared if history.decisions.get(r.alert_id) == "true_match"]
        # analysts mislabel a small share of alerts; disagreements beyond that share, or without a conflicting
        # structured field to show the customer, mean the threshold is too low (or the mapping is wrong)
        allowance = max(1, round(a["label_noise_allowance"] * len(cleared)))
        hard = all(any(c["source"] == "field" for c in r.conflicts) for r in cleared_matches)
        precision = 1 - len(cleared_matches) / len(cleared) if cleared else 1.0
        row = {
            "theta": theta,
            "cleared": len(cleared),
            "auto_clear": round(len(cleared) / max(len(results), 1), 4),
            "cleared_confirmed_matches": len(cleared_matches),
            "allowance": allowance,
            "all_hard": hard,
            "precision": round(precision, 4),
            "to_confirm": [r.alert_id for r in cleared_matches],
        }
        grid.append(row)
        if chosen is None and len(cleared_matches) <= allowance and hard and precision >= a["min_clear_precision"]:
            chosen = row
    report["backtest"] = {"alerts": len(results), "confirmed_matches": len(confirmed), "grid": grid}
    report["theta"] = chosen["theta"] if chosen else None
    if chosen:
        tpl2: Template = make_template({"theta": chosen["theta"]})
        sh = [r for s in shadow for r in tpl2.review(s).alerts]
        cleared_sh = [r for r in sh if r.disposition == "clear"]
        agree = sum(history.decisions.get(r.alert_id) == "false_positive" for r in cleared_sh)
        report["shadow"] = {
            "alerts": len(sh),
            "cleared": sum(r.disposition == "clear" for r in sh),
            "cleared_confirmed_matches": sum(
                r.disposition == "clear" and history.decisions.get(r.alert_id) == "true_match" for r in sh
            ),
            "clears_analysts_agree_with": round(agree / max(len(cleared_sh), 1), 4),
        }
    gate = [
        ("mapping parses and the date format is the only one the data allows", report["mapping"]["ok"]),
        ("a threshold meets the match and precision limits", chosen is not None),
    ]
    if chosen:
        gate.append(
            (
                "shadow month clears no analyst-confirmed match beyond the allowance",
                report["shadow"]["cleared_confirmed_matches"]
                <= max(1, round(a["label_noise_allowance"] * report["shadow"]["cleared"])),
            )
        )
    report["gate"] = [{"check": c, "ok": ok} for c, ok in gate]
    report["live"] = all(ok for _, ok in gate)
    return report
