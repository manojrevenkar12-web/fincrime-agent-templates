"""The one door to a model. Every call has a task, a tier and a prompt, and returns tokens, latency and cost.
Untrusted text (list remarks, articles) is rendered in marked blocks that the system prompt says not to obey."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Protocol

UNTRUSTED_OPEN = "<<untrusted"
UNTRUSTED_CLOSE = "<</untrusted>>"


@dataclass
class ModelRequest:
    task: str  # remarks | media
    tier: str
    system: str
    context: dict
    untrusted: list[dict] = field(default_factory=list)
    spotlight: bool = True

    def prompt(self) -> str:
        parts = [json.dumps(self.context, ensure_ascii=False, sort_keys=True)]
        for u in self.untrusted:
            if self.spotlight:
                head = f'{UNTRUSTED_OPEN} source="{u["source"]}" id="{u["id"]}">>'
                parts.append(f"{head}\n{u['text']}\n{UNTRUSTED_CLOSE}")
            else:
                parts.append(f"{u['source']} {u['id']}: {u['text']}")
        return "\n\n".join(parts)


@dataclass
class Completion:
    data: dict
    tier: str
    task: str
    in_tokens: int
    out_tokens: int
    latency_ms: float
    cost_eur: float


class ModelClient(Protocol):
    def complete(self, request: ModelRequest) -> Completion: ...


def tokens(text: str) -> int:
    return max(1, len(text) // 4)


def price(tiers: dict, tier: str, in_tok: int, out_tok: int) -> float:
    t = tiers[tier]
    return (in_tok * t["in_eur_per_m"] + out_tok * t["out_eur_per_m"]) / 1_000_000
