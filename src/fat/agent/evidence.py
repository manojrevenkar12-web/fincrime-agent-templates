"""Read-only access to what an investigator can see: list entries and articles, by id."""

from __future__ import annotations

import json
import re
from datetime import date
from functools import cache
from pathlib import Path


@cache
def load_jsonl(path: str) -> dict[str, dict]:
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            out[row["id"]] = row
    return out


class Lists:
    def __init__(self, path: Path):
        self.entries = load_jsonl(str(path))

    def get(self, entry_id: str) -> dict:
        return self.entries[entry_id]


class Media:
    def __init__(self, path: Path):
        self.articles = load_jsonl(str(path))

    def get(self, article_id: str) -> dict:
        return self.articles[article_id]


def entry_dobs(entry: dict) -> tuple[list[date], list[int]]:
    full, years = [], []
    for d in entry.get("dobs", []):
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            full.append(date.fromisoformat(d))
        elif re.fullmatch(r"\d{4}", d):
            years.append(int(d))
    return full, years


def entry_pob_city(entry: dict) -> str | None:
    pob = entry.get("pob")
    return pob.split(",")[0].strip() if pob else None


def age_at(dob: date, when: date) -> int:
    return when.year - dob.year - ((when.month, when.day) < (dob.month, dob.day))
