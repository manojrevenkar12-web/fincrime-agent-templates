"""The development evaluation: every design on months 1-6 of the development customers -> reports/dev.json."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fat import settings
from fat.evals.pipeline import dump, evaluate


def verdict(r: dict) -> str:
    return "SHIP" if r["gate"]["ship"] else "NO: " + str(r["gate"]["failed"])


if __name__ == "__main__":
    rt = settings.runtime()
    res = evaluate(rt["release"]["dev_tenants"], set(range(1, 7)))
    dump("dev", res)
    for v, r in res["variants"].items():
        a = r["all"]
        print(
            f"{v:20s} auto-clear {a['auto_clear']:.3f} matches cleared {a['matches_cleared']} breaches "
            f"{a['policy_breaches']} media closed {a['media_closed']:.3f} missed {a['missed_findings']} wrong "
            f"{a['wrong_person']} obeyed {a['obeyed']}/{a['injected']} hours/1000 {a['analyst_hours_per_1000']} "
            f"€/1000 {a['eur_per_1000']} p95 {a['p95_ms']} {verdict(r)}"
        )
