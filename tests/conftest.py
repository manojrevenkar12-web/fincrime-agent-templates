import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fat import settings  # noqa: E402


@pytest.fixture(scope="session")
def rt():
    return settings.runtime()


def history(tenant: str, n: int = 50) -> list[dict]:
    out = []
    with open(settings.DATA / "tenants" / tenant / "screenings.jsonl", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row["split"] == "history":
                out.append(row)
            if len(out) >= n:
                break
    return out
