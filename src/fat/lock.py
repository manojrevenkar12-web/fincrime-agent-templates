"""Fingerprints of the world data, pinned in config/heldout.lock before any agent code existed."""

from __future__ import annotations

import hashlib
import json

from . import settings


def _digest(paths) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(str(p.relative_to(settings.ROOT)).encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def current() -> dict:
    d = settings.DATA
    return {
        "world_config": _digest([settings.CONFIG / "world.toml"]),
        "lists": _digest(list((d / "lists").glob("*"))),
        "media": _digest(list((d / "media").glob("*"))),
        "tenants": _digest(list((d / "tenants").rglob("*.*"))),
        "truth": _digest(list((d / "truth").glob("*"))),
    }


def pinned() -> dict:
    return json.loads((settings.CONFIG / "heldout.lock").read_text())


def changed() -> list[str]:
    now, pin = current(), pinned()
    return [k for k in pin if now.get(k) != pin[k]]
