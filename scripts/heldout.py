"""Once: activate Northbank from its history, then run every design on months 7-8 of all four customers.

Refuses to run if the world data differs from config/heldout.lock, if code or config are not committed, or if
it has run before. Problems the run shows are published and fixed with tests on development data; the held-out
months are not run again."""

import datetime
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fat import lock, settings  # noqa: E402
from fat.evals.activate import run_activation  # noqa: E402
from fat.evals.pipeline import dump, evaluate  # noqa: E402

LOG = settings.REPORTS / "heldout-runs.log"


def verdict(r: dict) -> str:
    return "SHIP" if r["gate"]["ship"] else "NO: " + str(r["gate"]["failed"])


if __name__ == "__main__":
    if changed := lock.changed():
        sys.exit(f"held-out data differs from the pin: {changed}")
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "src", "config", "scripts"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    if dirty:
        sys.exit(f"commit code and config first:\n{dirty}")
    if LOG.exists() and LOG.read_text().strip():
        sys.exit("the held-out months have been run already; see reports/heldout-runs.log")
    rt = settings.runtime()
    northbank = run_activation("northbank", write=False)
    generic_nb = run_activation("northbank", "_generic", write=False)
    acts = {"northbank": {"theta": northbank["theta"], "live": northbank["live"]}}
    res = evaluate(rt["release"]["heldout_tenants"], {7, 8}, activations=acts)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    res |= {"commit": commit, "northbank_activation": northbank, "northbank_generic_activation": generic_nb}
    dump("heldout", res)
    stamp = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
    with open(LOG, "a") as fh:
        fh.write(f"{stamp} commit {commit} held-out run 1\n")
    print(
        "northbank activation:",
        "live" if northbank["live"] else "NOT LIVE",
        northbank["theta"],
        [g for g in northbank["gate"] if not g["ok"]],
    )
    print(
        "northbank generic:",
        "live" if generic_nb["live"] else "NOT LIVE",
        [g for g in generic_nb["gate"] if not g["ok"]],
    )
    for v, r in res["variants"].items():
        a = r["all"]
        print(
            f"{v:20s} auto-clear {a['auto_clear']:.3f} matches cleared {a['matches_cleared']} breaches "
            f"{a['policy_breaches']} media closed {a['media_closed']:.3f} missed {a['missed_findings']} wrong "
            f"{a['wrong_person']} obeyed {a['obeyed']}/{a['injected']} hours/1000 {a['analyst_hours_per_1000']} "
            f"€/1000 {a['eur_per_1000']} {verdict(r)}"
        )
