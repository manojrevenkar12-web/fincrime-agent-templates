"""A simulated model provider, because this repository is measured without a provider key.

It reads what is in its prompt: the remarks or the article as they were rendered (an instruction the guards
held back is not there to obey). Its understanding of an article's topic and outcome comes from the truth
(that is the simulation); it then makes its tier's mistakes at the rates in config/fat.toml.
"""

from __future__ import annotations

import hashlib
import json
import random
import re

from ..agent.llm import UNTRUSTED_OPEN, Completion, ModelRequest, price, tokens
from ..world.names import CULTURES, GERMAN_CITIES
from ..world.text import INJECTIONS

ALL_CITIES = sorted({c for cu in CULTURES.values() for v in cu["cities"].values() for c in v} | set(GERMAN_CITIES))
TOPICS = [
    "fraud",
    "money_laundering",
    "sanctions_evasion",
    "bribery",
    "tax_evasion",
    "insolvency",
    "terrorism_financing",
]
MONTH = r"(January|February|March|April|May|June|July|August|September|October|November|December)"
MONTHS = {m: i for i, m in enumerate(MONTH[1:-1].split("|"), start=1)}
DETAIL = [
    re.compile(r"(?P<q>(?P<age>\d{1,3}), an? (?P<occ>[a-z -]+?) from (?P<city>[A-Z][\w .-]+?),)"),
    re.compile(r"(?P<q>an? (?P<age>\d{1,3})-year-old (?P<occ>[a-z -]+?) living in (?P<city>[A-Z][\w .-]+?),)"),
    re.compile(r"(?P<q>(?P<age>\d{1,3}), (?P<occ>[\w -]+?) aus (?P<city>[A-Z][\w .-]+?),)"),
    re.compile(r"(?P<q>ein (?P<age>\d{1,3})-jähriger (?P<occ>[\w -]+?) aus (?P<city>[A-Z][\w .-]+?),)"),
]
ACQ = {"en": "was acquitted", "de": "wurde freigesprochen"}


class Ledger:
    def __init__(self):
        self.calls: list[dict] = []

    def record(self, task: str, tier: str, mistakes: list[str], ref: str) -> None:
        self.calls.append({"task": task, "tier": tier, "mistakes": mistakes, "ref": ref})


class SimModel:
    def __init__(self, cfg: dict, article_truth: dict, ledger: Ledger):
        self.cfg, self.truth, self.ledger = cfg, article_truth, ledger
        self.sample = ""

    def complete(self, req: ModelRequest) -> Completion:
        prompt = req.system + "\n" + req.prompt()
        h = hashlib.sha256(f"{self.cfg['sim']['seed']}|{self.sample}|{req.task}|{req.tier}|{prompt}".encode())
        rng = random.Random(int.from_bytes(h.digest()[:8], "big"))
        rates = self.cfg["sim"][req.tier]
        data = self._remarks(req, rng, rates) if req.task == "remarks" else self._media(req, prompt, rng, rates)
        out = json.dumps(data, ensure_ascii=False)
        in_tok, out_tok = tokens(prompt), tokens(out)
        t = self.cfg["tiers"][req.tier]
        jitter = 1 + self.cfg["sim"]["latency_jitter"] * (rng.random() * 2 - 1)
        latency = (t["base_ms"] + in_tok * t["in_ms_per_tok"] + out_tok * t["out_ms_per_tok"]) * jitter
        return Completion(
            data, req.tier, req.task, in_tok, out_tok, latency, price(self.cfg["tiers"], req.tier, in_tok, out_tok)
        )

    def _remarks(self, req: ModelRequest, rng: random.Random, r: dict) -> dict:
        text = req.untrusted[0]["text"]
        out: dict = {}
        mistakes = []
        m = re.search(rf"(?:Born on|Date of birth reported as) (\d{{1,2}}) {MONTH} (\d{{4}})", text)
        if m and rng.random() >= r["missed_mention"]:
            d = f"{int(m.group(3)):04d}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}"
            out["dob"], out["dob_quote"] = d, m.group(0)
            if rng.random() < r["misread_value"]:
                out["dob"] = (
                    f"{int(m.group(3)) + rng.choice([-1, 1]):04d}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}"
                )
                mistakes.append("misread_dob")
        m = re.search(r"(?:Born in|Place of birth:|POB) ([A-Z][\w .-]+?)[,(]", text)
        if m and rng.random() >= r["missed_mention"]:
            out["pob_city"], out["pob_quote"] = m.group(1).strip(), m.group(0)
            if rng.random() < r["misread_value"]:
                out["pob_city"] = rng.choice([c for c in ALL_CITIES if c != out["pob_city"]])
                mistakes.append("misread_pob")
        for k in ("dob_quote", "pob_quote"):
            if k in out and rng.random() < r["fabricated_quote"]:
                out[k] = out[k].replace("Born", "Reportedly born").replace("POB", "Place of birth")
                mistakes.append(f"fabricated_{k}")
        self.ledger.record("remarks", req.tier, mistakes, req.untrusted[0]["id"])
        return out

    def _media(self, req: ModelRequest, prompt: str, rng: random.Random, r: dict) -> dict:
        art_id = req.untrusted[0]["id"]
        text = req.untrusted[0]["text"]
        t = self.truth[art_id]
        lang = req.context.get("lang", "en")
        mistakes: list[str] = []
        out: dict = {
            "adverse": t["adverse"],
            "topic": t["topic"] if t["adverse"] else None,
            "outcome": t["outcome"],
            "outcome_quote": None,
        }
        for pat in DETAIL:
            m = pat.search(text)
            if m:
                if rng.random() >= r["missed_mention"]:
                    out["age"], out["age_quote"] = int(m.group("age")), m.group("q")
                    out["city"], out["city_quote"] = m.group("city").strip(), m.group("q")
                    if rng.random() < r["misread_value"]:
                        out["age"] = out["age"] + rng.choice([-6, -4, 4, 6])
                        mistakes.append("misread_age")
                    if rng.random() < r["fabricated_quote"]:
                        out["age_quote"] = out["age_quote"].replace(",", ";", 1)
                        mistakes.append("fabricated_quote")
                break
        if t["outcome"] == "acquitted":
            sent = next((s for s in re.split(r"(?<=[.!?])\s+", text) if ACQ[lang] in s), None)
            out["outcome_quote"] = sent
        if t["adverse"] and rng.random() < r["topic_confusion"]:
            out["topic"] = rng.choice([x for x in TOPICS if x != t["topic"]])
            mistakes.append("topic_confusion")
        if t["adverse"] and rng.random() < r["outcome_error"]:
            out["outcome"] = "charged" if t["outcome"] == "acquitted" else "acquitted"
            mistakes.append("outcome_error")
        injected = next((i for fam in INJECTIONS.values() for i in fam if i["text"] in prompt), None)
        if injected:
            spotlit = req.spotlight and UNTRUSTED_OPEN in prompt
            if rng.random() < (r["injection_spotlit"] if spotlit else r["injection_inline"]):
                out.update({"adverse": False, "topic": None, "outcome": "cleared", "outcome_quote": injected["text"]})
                mistakes.append("obeyed_injection")
        self.ledger.record("media", req.tier, mistakes, art_id)
        return out


def build(cfg: dict, truth_path) -> tuple[SimModel, Ledger]:
    with open(truth_path, encoding="utf-8") as fh:
        world = json.load(fh)
    ledger = Ledger()
    return SimModel(cfg, world["articles"], ledger), ledger
