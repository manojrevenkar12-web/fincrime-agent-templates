"""Activate the template for customers: python scripts/activate.py finvia ledgerly kreditwerk
With --generic, run the activation checks on the generic config instead (nothing is written)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fat import settings
from fat.evals.activate import run_activation

if __name__ == "__main__":
    generic = "--generic" in sys.argv
    tenants = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = {}
    for t in tenants:
        rep = run_activation(t, "_generic" if generic else None)
        out[t] = rep
        print(
            t,
            "live" if rep["live"] else "NOT LIVE",
            "theta",
            rep["theta"],
            rep["mapping"]["formats_the_data_allows"],
            rep["mapping"]["formats_the_parser_uses"],
            rep["mapping"]["dob_parse_rate"],
            [g for g in rep["gate"] if not g["ok"]],
            rep.get("shadow"),
            f"{rep['seconds']}s",
            rep["config_lines"],
            "config lines",
        )
    name = "activation-generic" if generic else "activation"
    path = settings.REPORTS / f"{name}.json"
    prev = json.loads(path.read_text()) if path.exists() else {}
    path.write_text(json.dumps({**prev, **out}, indent=1) + "\n")
