"""reports/results.json, reports/RESULTS.md, the README results block and the dashboard's data, all generated
from reports/dev.json, reports/heldout.json, reports/activation*.json and config/routing.json."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fat import settings  # noqa: E402

ORDER = ["analysts-only", "rules-only", "generic", "activated", "activated-no-guards"]
NAMES = {
    "finvia": "Finvia (neobank)",
    "ledgerly": "Ledgerly (B2B spend)",
    "kreditwerk": "Kreditwerk (SME lender)",
    "northbank": "Northbank (retail bank, held out)",
}


def load(name: str) -> dict | None:
    p = settings.REPORTS / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def pct(x: float, d: int = 1) -> str:
    return f"{100 * x:.{d}f}%"


def table(rep: dict) -> list[str]:
    rows = [
        "| Design | Alerts closed without review | True matches closed | Closed against policy | Media hits "
        "closed | Findings missed | Instructions obeyed | Analyst hours per 1,000 screenings | Model cost per "
        "1,000 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for v in ORDER:
        r = rep["variants"][v]
        a = r["all"]
        name = f"**{r['label']}**" if v == "activated" else r["label"]
        rows.append(
            f"| {name} | {pct(a['auto_clear'])} ({pct(a['auto_clear_ci'][0], 0)}–{pct(a['auto_clear_ci'][1], 0)}) "
            f"| {a['matches_cleared']} of {a['true_matches']} | {a['policy_breaches']} | "
            f"{pct(a['media_closed'])} | {a['missed_findings']} of {a['true_findings']} | "
            f"{a['obeyed']} of {a['injected']} | {a['analyst_hours_per_1000']:.0f} | €{a['eur_per_1000']:.2f} |"
        )
    return rows


def per_customer(rep: dict) -> list[str]:
    rows = [
        "| Customer | Screenings | Alerts | Closed by the template | Closable under the customer's policy | "
        "Rules only | Same agent, one config | Analyst hours per 1,000: before → after |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for t in rep["tenants"]:
        act = rep["variants"]["activated"]["tenants"][t]
        rules = rep["variants"]["rules-only"]["tenants"][t]
        gen = rep["variants"]["generic"]["tenants"][t]
        base = rep["variants"]["analysts-only"]["tenants"][t]
        gen_note = pct(gen["auto_clear"])
        if gen["matches_cleared"]:
            gen_note += f", {gen['matches_cleared']} true matches closed"
        if gen["policy_breaches"]:
            gen_note += f", {gen['policy_breaches']} against policy"
        rows.append(
            f"| {NAMES[t]} | {act['screenings']} | {act['alerts']} | {pct(act['auto_clear'])} | "
            f"{pct(act['clearable_share'])} | {pct(rules['auto_clear'])} | {gen_note} | "
            f"{base['analyst_hours_per_1000']:.0f} → {act['analyst_hours_per_1000']:.0f} |"
        )
    return rows


def gate_rows(rep: dict, split: str) -> list[str]:
    out = []
    for v in ORDER:
        r = rep["variants"][v]
        why = "every check passes" if r["gate"]["ship"] else "fails: " + ", ".join(r["gate"]["failed"])
        out.append(f"| {split}: {r['label']} | {'**SHIP**' if r['gate']['ship'] else '**NO-SHIP**'} | {why} |")
    return out


def activation_rows(acts: dict, generic: dict, held: dict | None) -> list[str]:
    rows = [
        "| Customer | Config lines | Mapping check | Threshold | Shadow month: clears analysts agree with | Live | "
        "Same checks on the one-size config |",
        "|---|---|---|---|---|---|---|",
    ]
    items = [(t, acts.get(t), generic.get(t)) for t in ("finvia", "ledgerly", "kreditwerk")]
    if held:
        items.append(("northbank", held["northbank_activation"], held["northbank_generic_activation"]))
    for t, a, g in items:
        if not a:
            continue
        m = a["mapping"]
        check = "passes" if m["ok"] else f"fails ({', '.join(m['formats_the_parser_uses'])})"
        g_note = (
            "live"
            if g and g["live"]
            else "not live: " + "; ".join(x["check"] for x in g["gate"] if not x["ok"])
            if g
            else "–"
        )
        shadow = a.get("shadow", {})
        rows.append(
            f"| {NAMES[t]} | {a['config_lines']} | {check} | {a['theta']} | "
            f"{pct(shadow.get('clears_analysts_agree_with', 0))} of {shadow.get('cleared', 0)} | "
            f"{'yes' if a['live'] else 'no'}, {a['seconds']} s | {g_note} |"
        )
    return rows


def main() -> None:
    dev, held = load("dev"), load("heldout")
    acts, generic = load("activation") or {}, load("activation-generic") or {}
    routing = json.loads((settings.CONFIG / "routing.json").read_text())
    res = {"dev": dev, "heldout": held, "activation": acts, "activation_generic": generic, "routing": routing}
    (settings.REPORTS / "results.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
    head = held or dev
    lines = ["<!-- results:start (generated by make report) -->"]
    if held:
        lines += [
            f"Held-out run (`{held['commit'][:7]}`, once): months 7-8 of all four customers, including Northbank, "
            "whose data the template never saw before this run and which was activated inside it.",
            "",
        ]
    lines += table(head) + [
        "",
        "In brackets: 95% interval. Workload counts 6 minutes per alert and 3 per media hit "
        "an analyst has to look at (an assumption in config).",
        "",
    ]
    lines += per_customer(head) + [""]
    lines += ["| Release decision | Verdict | Why |", "|---|---|---|"]
    if held:
        lines += gate_rows(held, "Held-out")
    lines += gate_rows(dev, "Development") + ["<!-- results:end -->"]
    block = "\n".join(lines)
    readme = ROOT / "README.md"
    if readme.exists():
        readme.write_text(
            re.sub(r"<!-- results:start.*?<!-- results:end -->", lambda _: block, readme.read_text(), flags=re.S)
        )
    md = ["# Results", "", "Generated by `make report`.", ""]
    for name, rep in (
        ("Held-out (months 7-8, four customers)", held),
        ("Development (months 1-6, three customers)", dev),
    ):
        if rep:
            md += [f"## {name}", ""] + table(rep) + [""] + per_customer(rep) + [""]
    md += ["## Activation", ""] + activation_rows(acts, generic, held) + [""]
    md += [
        "## Model tiers (development history)",
        "",
        "| Task | Target | small | medium | large | Chosen |",
        "|---|---|---|---|---|---|",
    ]
    for task, t in routing["measured"].items():
        cells = " | ".join(f"{pct(r['rate'])} (≥ {pct(r['lower'])})" for r in t["tiers"])
        md.append(
            f"| {task} | {pct(t['target'], 0)} | {cells} | {t['chosen']}"
            f"{'' if t['meets_target'] else ' (closest; none meets the target)'} |"
        )
    (settings.REPORTS / "RESULTS.md").write_text("\n".join(md) + "\n")
    web = ROOT / "web" / "public" / "data"
    web.mkdir(parents=True, exist_ok=True)
    slim = {
        "heldout": held and {k: held[k] for k in ("variants", "tenants", "commit")},
        "dev": {k: dev[k] for k in ("variants", "tenants")},
        "activation": [
            {
                "tenant": t,
                **{k: a[k] for k in ("config_lines", "theta", "live", "seconds")},
                "mapping_ok": a["mapping"]["ok"],
                "shadow": a.get("shadow", {}),
                "generic_live": (generic.get(t) or {}).get("live"),
            }
            for t, a in [*acts.items(), *([("northbank", held["northbank_activation"])] if held else [])]
        ],
        "routing": routing["measured"],
    }
    if held:
        slim["activation"][-1]["generic_live"] = held["northbank_generic_activation"]["live"]
    (web / "results.json").write_text(json.dumps(slim, ensure_ascii=False) + "\n")
    print("wrote reports/results.json, reports/RESULTS.md, the README block, web/public/data/results.json")


if __name__ == "__main__":
    main()
