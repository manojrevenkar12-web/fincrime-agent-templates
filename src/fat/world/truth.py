"""What a perfect reviewer could conclude from the evidence the platform can see, under each customer's policy."""

from __future__ import annotations

from datetime import date


def person_conflicts(subject: dict, facts: dict) -> list[str]:
    """Hard identifiers that differ. Dates of birth tolerate one year when the list gives only a year."""
    out = []
    if facts.get("dob_full"):
        if subject["dob"] not in facts["dob_full"]:
            out.append("dob")
    elif facts.get("dob_years"):
        y = int(subject["dob"][:4])
        if all(abs(y - int(x)) >= 2 for x in facts["dob_years"]):
            out.append("dob")
    if facts.get("pob_city") and facts["pob_city"] != subject["pob_city"]:
        out.append("pob")
    return out


def entity_conflicts(company: dict, facts: dict) -> list[str]:
    out = []
    if facts.get("registration") and company["reg_number"] not in facts["registration"]:
        out.append("registration")
    if facts.get("country") and facts["country"] != company["country"]:
        out.append("country")
    return out


def alert_ideal(is_match: bool, conflicts: list[str], policy: dict) -> str:
    if is_match:
        return "escalate"
    return "clear" if len(conflicts) >= policy["clear_conflicts"] else "escalate"


def in_scope(article: dict, truth: dict, screened_on: str, policy: dict) -> bool:
    if not truth["adverse"] or truth["topic"] not in policy["topics"] or truth["outcome"] == "acquitted":
        return False
    d, s = date.fromisoformat(article["published"]), date.fromisoformat(screened_on)
    return (s - d).days <= policy["lookback_years"] * 365


def media_ideal(party_id: str, hits: list[dict], articles: dict, art_truth: dict, screened_on: str,
                policy: dict) -> tuple[str, list[str]]:
    """'finding' if an identifiable in-scope article is about the party; 'escalate' if an in-scope article
    cannot be attributed either way; otherwise 'clear'. Returns the finding article ids."""
    findings, unsure = [], []
    for h in hits:
        a, t = articles[h["article_id"]], art_truth[h["article_id"]]
        if not in_scope(a, t, screened_on, policy):
            continue
        if not t["identifying"]:
            unsure.append(a["id"])
        elif t["subject"] == party_id:
            findings.append(a["id"])
    if findings:
        return "finding", sorted(findings)
    return ("escalate" if unsure else "clear"), []
