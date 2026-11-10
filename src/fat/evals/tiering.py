"""Which model tier reads remarks and articles? The cheapest whose pass rate, at its 95% lower bound on the
development customers' history, meets the task's target. Written to config/routing.json with the numbers."""

from __future__ import annotations

import json

from .. import settings
from ..agent.evidence import Lists, Media
from ..agent.guards import quoted
from ..agent.llm import ModelRequest
from ..agent.template import MEDIA_SYSTEM, REMARKS_SYSTEM
from ..sim.model import build as build_sim
from .run import screenings, world_truth
from .stats import wilson


def measure() -> dict:
    rt = settings.runtime()
    model, _ = build_sim(rt, settings.DATA / "truth" / "world.json")
    lists, media = Lists(settings.ROOT / rt["paths"]["lists"]), Media(settings.ROOT / rt["paths"]["media"])
    W = world_truth()
    facts, arts = W["list_facts"], W["articles"]
    entry_ids, article_ids = set(), set()
    for t in rt["release"]["dev_tenants"]:
        for s in screenings(t):
            if s["split"] != "history":
                continue
            entry_ids |= {a["entry_id"] for a in s["alerts"] if lists.get(a["entry_id"]).get("remarks")}
            article_ids |= {h["article_id"] for h in s.get("media_hits", [])}
    entries = sorted(e for e in entry_ids if lists.get(e)["type"] == "person")
    out = {"remarks": {}, "media": {}}
    for tier in rt["routing"]["tiers"]:
        ok = n = 0
        for e in entries:
            entry = lists.get(e)
            c = model.complete(
                ModelRequest(
                    "remarks",
                    tier,
                    REMARKS_SYSTEM,
                    {"entry": e},
                    [{"id": e, "source": "list-remarks", "text": entry["remarks"]}],
                )
            )
            d, f = c.data, facts[e]
            want_pob = f.get("pob_city") if not entry.get("pob") else None
            want_dob = f["dob_full"][0] if f.get("dob_full") and not entry.get("dobs") else None
            good = (
                d.get("pob_city") == want_pob
                and (want_pob is None or quoted(entry["remarks"], d.get("pob_quote"), want_pob))
                and d.get("dob") == want_dob
                and (want_dob is None or quoted(entry["remarks"], d.get("dob_quote")))
            )
            ok += good
            n += 1
        out["remarks"][tier] = (ok, n)
        ok = n = 0
        for a in sorted(article_ids):
            art, t = media.get(a), arts[a]
            c = model.complete(
                ModelRequest(
                    "media",
                    tier,
                    MEDIA_SYSTEM,
                    {"article": a, "published": art["published"], "lang": art["lang"]},
                    [{"id": a, "source": "news-article", "text": art["body"]}],
                )
            )
            d = c.data
            good = d.get("adverse") == t["adverse"] and (
                not t["adverse"] or (d.get("topic") == t["topic"] and d.get("outcome") == t["outcome"])
            )
            if t["identifying"]:
                good = good and d.get("age") is not None and quoted(art["body"], d.get("age_quote"), str(d["age"]))
            ok += good
            n += 1
        out["media"][tier] = (ok, n)
    decision, table = {}, {}
    for task, by_tier in out.items():
        target = rt["routing"]["target"][task]
        rows, chosen = [], None
        for tier in rt["routing"]["tiers"]:
            k, n = by_tier[tier]
            lo, _ = wilson(k, n, rt["routing"]["confidence"])
            rows.append({"tier": tier, "passed": k, "n": n, "rate": round(k / n, 4), "lower": round(lo, 4)})
            if chosen is None and lo >= target:
                chosen = tier
        meets = chosen is not None
        chosen = chosen or max(rows, key=lambda r: r["lower"])["tier"]
        decision[task] = chosen
        table[task] = {"target": target, "tiers": rows, "chosen": chosen, "meets_target": meets}
    return {"routing": decision, "measured": table, "how": "development customers' history, one call per item"}


def main() -> None:
    res = measure()
    (settings.CONFIG / "routing.json").write_text(json.dumps(res, indent=1) + "\n")
    for task, t in res["measured"].items():
        print(task, t["chosen"], [(r["tier"], r["rate"], r["lower"]) for r in t["tiers"]])


if __name__ == "__main__":
    main()
