"""The customer's screening provider: fuzzy name matching against the lists, tuned for recall.

It folds diacritics, sorts name tokens and drops legal forms, then alerts on every list name whose
token-set similarity reaches the threshold. Like real providers it knows nothing about dates of birth
or places, which is why most of its alerts are false positives.
"""

from __future__ import annotations

import re
import unicodedata

from rapidfuzz import fuzz, process

SPECIAL = str.maketrans({"ß": "ss", "ı": "i", "ş": "s", "ğ": "g", "ç": "c", "ø": "o", "ł": "l"})
LEGAL = {"LLC", "L", "C", "FZE", "F", "Z", "E", "GMBH", "G", "M", "B", "H", "UG", "LTD", "LIMITED", "OOO", "SRL",
         "SAL", "AS", "A", "S", "STI", "SL"}


def fold(name: str) -> str:
    t = unicodedata.normalize("NFKD", name.translate(SPECIAL).replace("ü", "u").replace("ö", "o").replace("ä", "a"))
    t = "".join(ch for ch in t if not unicodedata.combining(ch)).upper()
    return re.sub(r"[^A-Z0-9 ]+", " ", t)


def key(name: str, kind: str) -> str:
    tokens = fold(name).split()
    if kind == "entity":
        tokens = [x for x in tokens if x not in LEGAL]
    return " ".join(sorted(tokens))


def _score(a: str, b: str, **kw) -> float:
    """Token-set similarity: a list name with an extra middle name still matches the customer's name."""
    return fuzz.token_set_ratio(a, b, **kw) / 100


class Provider:
    def __init__(self, entries: list[dict], threshold: float):
        self.threshold = threshold
        self.index: dict[str, list[tuple[str, str, dict]]] = {"person": [], "entity": []}
        for e in entries:
            for n in e["names"]:
                self.index[e["type"]].append((key(n, e["type"]), n, e))
        self.keys = {k: [x[0] for x in v] for k, v in self.index.items()}

    def screen(self, name: str, kind: str) -> list[dict]:
        best: dict[str, dict] = {}
        q = key(name, kind)
        for _, score, i in process.extract(q, self.keys[kind], scorer=_score, score_cutoff=self.threshold,
                                           limit=None):
            _, matched, e = self.index[kind][i]
            if e["id"] not in best or score > best[e["id"]]["score"]:
                best[e["id"]] = {"entry_id": e["id"], "list": e["source"], "matched_name": matched,
                                 "score": round(score, 4)}
        return sorted(best.values(), key=lambda h: -h["score"])


class MediaProvider:
    """The customer's media data provider: articles tagged with a person whose name is close to the query."""

    def __init__(self, articles: list[dict], threshold: float):
        self.threshold = threshold
        self.articles = articles
        self.keys = [key(a["persons"][0], "person") for a in articles]

    def search(self, name: str, before: str) -> list[dict]:
        hits = []
        for _, score, i in process.extract(key(name, "person"), self.keys, scorer=_score,
                                           score_cutoff=self.threshold, limit=None):
            a = self.articles[i]
            if a["published"] <= before:
                hits.append({"article_id": a["id"], "score": round(score, 4)})
        return sorted(hits, key=lambda h: h["article_id"])
