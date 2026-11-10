"""Run the activation pipeline for a customer (or the generic config on a customer's history) and record it."""

from __future__ import annotations

import json
import time

from .. import settings
from ..agent.activation import History, activate
from ..sim.model import build as build_sim
from .run import make, routing


def run_activation(tenant: str, config: str | None = None, write: bool = True) -> dict:
    rt = settings.runtime()
    model, _ = build_sim(rt, settings.DATA / "truth" / "world.json")
    customer = settings.customer(config or tenant)
    history = History.load(settings.DATA / "tenants" / tenant)
    variant = "generic" if config == "_generic" else "activated"
    t0 = time.perf_counter()

    def make_template(act: dict):
        tpl = make(variant, tenant, model, rt, act=act, route=routing())
        return tpl

    report = activate(customer, rt, history, make_template)
    report["seconds"] = round(time.perf_counter() - t0, 2)
    report["config_lines"] = sum(
        1
        for line in (settings.CONFIG / "customers" / f"{config or tenant}.toml").read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    )
    if write and config is None:
        out = settings.CONFIG / "activations"
        out.mkdir(exist_ok=True)
        (out / f"{tenant}.json").write_text(
            json.dumps({"theta": report["theta"], "live": report["live"], "report": report}, indent=1) + "\n"
        )
    return report
