"""CI gate: the candidate design on the development months; exits 1 if any check fails."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fat import settings
from fat.evals.pipeline import evaluate

if __name__ == "__main__":
    rt = settings.runtime()
    res = evaluate(rt["release"]["dev_tenants"], set(range(1, 7)))
    g = res["variants"][rt["release"]["candidate"]]["gate"]
    for c in g["checks"]:
        print("ok  " if c["ok"] else "FAIL", c["check"], c["value"], "limit", c["limit"])
    sys.exit(0 if g["ship"] else 1)
