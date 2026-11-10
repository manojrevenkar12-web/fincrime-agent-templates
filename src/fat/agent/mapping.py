"""From a customer's export to the template's parties. Explicit mappings come from the customer's data
dictionary; the `auto` mode guesses field names and date formats, as a template without an activation does."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime

SPECIAL = str.maketrans({"ß": "ss", "ı": "i", "ş": "s", "ğ": "g", "ç": "c", "ø": "o", "ł": "l"})

ALPHA3 = {
    "SYR": "SY",
    "IRQ": "IQ",
    "LBN": "LB",
    "ARE": "AE",
    "EGY": "EG",
    "JOR": "JO",
    "RUS": "RU",
    "UKR": "UA",
    "BLR": "BY",
    "KAZ": "KZ",
    "DEU": "DE",
    "AUT": "AT",
    "CHE": "CH",
    "ROU": "RO",
    "MDA": "MD",
    "TUR": "TR",
    "ESP": "ES",
    "MEX": "MX",
    "VEN": "VE",
    "COL": "CO",
    "GBR": "UK",
    "CYP": "CY",
}
DE_ADJECTIVE = {
    "syrisch": "SY",
    "irakisch": "IQ",
    "libanesisch": "LB",
    "emiratisch": "AE",
    "ägyptisch": "EG",
    "jordanisch": "JO",
    "russisch": "RU",
    "ukrainisch": "UA",
    "belarussisch": "BY",
    "kasachisch": "KZ",
    "deutsch": "DE",
    "österreichisch": "AT",
    "schweizerisch": "CH",
    "rumänisch": "RO",
    "moldauisch": "MD",
    "türkisch": "TR",
    "spanisch": "ES",
    "mexikanisch": "MX",
    "venezolanisch": "VE",
    "kolumbianisch": "CO",
    "britisch": "UK",
    "zyprisch": "CY",
}

AUTO = {
    "person_path": ["parties", "persons", "directors", "officers"],
    "given": ["first_name", "given_name", "firstname", "forename"],
    "surname": ["last_name", "surname", "family_name", "lastname"],
    "full_name": ["full_name", "name", "customer_name"],
    "dob": ["birth_date", "date_of_birth", "dob", "birthdate"],
    "pob_city": ["birth_place", "place_of_birth", "city_of_birth", "pob"],
    "residence_city": ["residence", "city", "address", "addr"],
    "nationality": ["nationality", "nat", "citizenship"],
    "company_name": ["legal_name", "company_name", "name", "company"],
    "registration": ["reg_no", "registration_number", "company_number"],
    "country": ["country", "country_of_registration"],
    "role": ["role"],
}


def fold(name: str) -> str:
    t = name.translate(SPECIAL).replace("ü", "u").replace("ö", "o").replace("ä", "a")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch)).upper()
    return re.sub(r"[^A-Z0-9 ]+", " ", t)


def name_key(name: str) -> str:
    return " ".join(sorted(fold(name).split()))


@dataclass
class Party:
    role: str
    kind: str  # person | entity
    name: str
    dob: date | None = None
    pob_city: str | None = None
    residence_city: str | None = None
    nationality: str | None = None
    occupation: str | None = None
    registration: str | None = None
    country: str | None = None

    @property
    def key(self) -> str:
        return name_key(self.name)


@dataclass
class Parsed:
    parties: list[Party]
    issues: list[str] = field(default_factory=list)


class Mapping:
    def __init__(self, cfg: dict, date_formats: list[str]):
        self.m = cfg["mapping"]
        self.auto = self.m.get("mode") == "auto"
        self.date_formats = date_formats

    def _field(self, rec: dict, name: str):
        if not self.auto:
            path = self.m.get(name)
            return rec.get(path) if path else None
        for cand in AUTO.get(name, []):
            if cand in rec:
                return rec[cand]
        return None

    def _date(self, value) -> date | None:
        if not value:
            return None
        formats = [self.m["dob_format"]] if not self.auto and self.m.get("dob_format") else self.date_formats
        for f in formats:
            try:
                return datetime.strptime(str(value), f).date()
            except ValueError:
                continue
        return None

    def _nationality(self, value) -> str | None:
        if not value:
            return None
        code = self.m.get("nationality_code", "alpha2") if not self.auto else "alpha2"
        v = str(value)
        if code == "alpha3":
            return ALPHA3.get(v.upper())
        if code == "de_adjective":
            return DE_ADJECTIVE.get(v.lower())
        return v.upper() if len(v) == 2 else None

    def _name(self, rec: dict) -> str | None:
        g, s = self._field(rec, "given"), self._field(rec, "surname")
        if g and s:
            return f"{g} {s}"
        full = self._field(rec, "full_name")
        if not full:
            return None
        order = self.m.get("name_order", "given_surname") if not self.auto else "given_surname"
        if order == "surname/given" and "/" in full:
            sn, g = full.split("/", 1)
            full = f"{g} {sn}"
        return " ".join(w.capitalize() if w.isupper() else w for w in str(full).replace("/", " ").split())

    def _person(self, rec: dict, role: str) -> Party:
        res = self._field(rec, "residence_city")
        return Party(
            role=str(self._field(rec, "role") or role),
            kind="person",
            name=self._name(rec) or "",
            dob=self._date(self._field(rec, "dob")),
            pob_city=self._field(rec, "pob_city"),
            residence_city=str(res).split(",")[0].strip() if res else None,
            nationality=self._nationality(self._field(rec, "nationality")),
            occupation=self._field(rec, "occupation"),
        )

    def parse(self, rec: dict) -> Parsed:
        issues: list[str] = []
        parties: list[Party] = []
        segment = (
            self.m.get("segment")
            if not self.auto
            else ("businesses" if self._people_list(rec) is not None else "individuals")
        )
        if segment == "individuals":
            parties.append(self._person(rec, "customer"))
        else:
            name = self._field(rec, "company_name")
            parties.append(
                Party(
                    role="company",
                    kind="entity",
                    name=str(name or ""),
                    registration=self._field(rec, "registration"),
                    country=self._field(rec, "country"),
                )
            )
            people = self._people_list(rec)
            if people is None:
                issues.append("no list of people found in the record")
            for p in people or []:
                parties.append(self._person(p, "person"))
        for p in parties:
            if p.kind == "person" and p.dob is None:
                issues.append(f"no date of birth for {p.name or 'a party'}")
        return Parsed(parties, issues)

    def _people_list(self, rec: dict) -> list | None:
        if not self.auto:
            path = self.m.get("person_path")
            return rec.get(path) if path else None
        for cand in AUTO["person_path"]:
            if isinstance(rec.get(cand), list):
                return rec[cand]
        return None


def party_for(parsed: Parsed, screened_name: str) -> Party | None:
    """The party the provider screened under this name: same tokens, or the closest token set."""
    k = name_key(screened_name)
    for p in parsed.parties:
        if p.key == k:
            return p
    toks = set(k.split())
    best = max(parsed.parties, key=lambda p: len(toks & set(p.key.split())), default=None)
    return best if best and toks & set(best.key.split()) else None
