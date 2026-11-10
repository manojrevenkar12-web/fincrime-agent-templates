"""Settings come from config/; nothing tunable lives in code."""

from __future__ import annotations

import tomllib
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
DATA = ROOT / "data"
REPORTS = ROOT / "reports"


@cache
def load(name: str) -> dict:
    with open(CONFIG / f"{name}.toml", "rb") as fh:
        return tomllib.load(fh)


def world() -> dict:
    return load("world")


def runtime() -> dict:
    return load("fat")


def customer(name: str) -> dict:
    return load(f"customers/{name}")
