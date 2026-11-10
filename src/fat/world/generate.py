"""Generate the world: screening lists, a media corpus, four customers' screenings and the truth.

Inputs (what the platform may read) go to data/lists, data/media and data/tenants/<id>; the truth goes to
data/truth. A list entry or an article never says which person it is about; only the truth does.
"""

from __future__ import annotations

import calendar
import json
import random
import string
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path

from .names import COMPANY_KINDS, COMPANY_WORDS, CULTURES, GERMAN_CITIES, LEGAL_FORMS, LEGAL_VARIANTS, OCCUPATIONS
from .screening import MediaProvider, Provider
from .truth import alert_ideal, entity_conflicts, media_ideal, person_conflicts
from .text import ARTICLE, COUNTRY_NAMES, INJECTIONS, NATIONALITY_DE, POLICIES, REMARKS

TOPICS_ADVERSE = ["fraud", "money_laundering", "sanctions_evasion", "bribery", "tax_evasion", "insolvency",
                  "terrorism_financing"]
TOPICS_NEUTRAL = ["sports", "business_award", "local_news", "charity"]
PROGRAMS = {"arabic": ["SYR", "SDGT", "IRAQ"], "slavic": ["RUSSIA-EO14024", "UKRAINE-EO13660", "BELARUS"],
            "turkish": ["SDGT"], "spanish": ["VENEZUELA", "SDNTK"], "romanian": ["MOLDOVA"], "german": ["CYBER"]}
SOURCES = ["OFAC", "EU", "UK", "UN"]


@dataclass
class Subject:
    id: str
    culture: str
    gender: str
    given: str
    surname: str
    dob: date
    pob_city: str
    pob_country: str
    nationality: str
    occupation: str
    residence_city: str
    residence_country: str
    id_number: str = ""

    def age_at(self, d: date) -> int:
        return d.year - self.dob.year - ((d.month, d.day) < (self.dob.month, self.dob.day))


@dataclass
class Company:
    id: str
    name_word: str
    kind: str
    legal_form: str
    country: str
    city: str
    reg_number: str
    owners: list[str] = field(default_factory=list)


class World:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.rng = random.Random(cfg["world"]["seed"])
        self.subjects: dict[str, Subject] = {}
        self.companies: dict[str, Company] = {}
        self.n = 0

    # -- people and names ----------------------------------------------------------------------
    def new_subject(self, culture: str, born_from: int = 1950, born_to: int = 2003, country: str | None = None) -> Subject:
        r = self.rng
        c = CULTURES[culture]
        gender = "m" if r.random() < 0.65 else "f"
        given = r.choice(sorted(c["given_m" if gender == "m" else "given_f"]))
        surname = r.choice(sorted(c["surnames"]))
        nat = country or r.choice(c["countries"])
        pob_city = r.choice(c["cities"].get(nat, c["cities"][c["countries"][0]]))
        start = date(born_from, 1, 1)
        dob = start + timedelta(days=r.randrange((date(born_to, 12, 31) - start).days))
        self.n += 1
        s = Subject(f"P{self.n:06d}", culture, gender, given, surname, dob, pob_city, nat, nat,
                    r.choice(OCCUPATIONS), r.choice(GERMAN_CITIES), "DE",
                    "".join(r.choices(string.ascii_uppercase + string.digits, k=9)))
        self.subjects[s.id] = s
        return s

    def surname_form(self, s: Subject, part: str) -> str:
        if s.gender == "f" and CULTURES[s.culture].get("feminine_suffix") and not part.endswith("enko"):
            return part + "a"
        return part

    def render(self, s: Subject, canonical_share: float | None = None) -> tuple[str, str]:
        """A spelling of the subject's name: canonical with the configured share, otherwise a variant."""
        r = self.rng
        share = self.cfg["screening"]["canonical_spelling_share"] if canonical_share is None else canonical_share
        c = CULTURES[s.culture]
        given_pool = c["given_m" if s.gender == "m" else "given_f"]
        g = s.given if r.random() < share or not given_pool[s.given] else r.choice(given_pool[s.given])
        sn = s.surname if r.random() < share or not c["surnames"][s.surname] else r.choice(c["surnames"][s.surname])
        return g, self.surname_form(s, sn)

    def namesake(self, s: Subject) -> Subject:
        """A different person with the same name: different birth date, usually a different city."""
        t = self.new_subject(s.culture)
        t.gender, t.given, t.surname = s.gender, s.given, s.surname
        while abs(t.dob.year - s.dob.year) < 4:
            t.dob = date(self.rng.randint(1950, 2003), t.dob.month, min(t.dob.day, 28))
        return t

    def new_company(self, country: str, city: str) -> Company:
        r = self.rng
        self.n += 1
        kind = r.choice(sorted(COMPANY_KINDS))
        forms = LEGAL_FORMS.get(country, ["Ltd"])
        reg = f"HRB {r.randint(10000, 99999)}" if country == "DE" else f"{country}{r.randint(1000000, 9999999)}"
        word = r.choice(COMPANY_WORDS) if r.random() < 0.3 else " ".join(r.sample(COMPANY_WORDS, 2))
        co = Company(f"C{self.n:06d}", word, kind, r.choice(forms), country, city, reg)
        self.companies[co.id] = co
        return co

    def company_name(self, co: Company, canonical: bool = True) -> str:
        r = self.rng
        kind = co.kind if canonical or not COMPANY_KINDS[co.kind][1:] else r.choice(COMPANY_KINDS[co.kind])
        form = co.legal_form if canonical or co.legal_form not in LEGAL_VARIANTS else r.choice(
            LEGAL_VARIANTS[co.legal_form])
        return f"{co.name_word} {kind} {form}"

    # -- lists -----------------------------------------------------------------------------------
    def make_lists(self) -> tuple[list[dict], dict[str, str]]:
        r, lc = self.rng, self.cfg["lists"]
        entries, truth = [], {}
        self.facts: dict[str, dict] = {}
        cultures, weights = zip(*lc["culture_weights"].items(), strict=True)
        for i in range(lc["sanctioned_persons"]):
            s = self.new_subject(r.choices(cultures, weights)[0], 1940, 1995)
            entry_id = f"SAN-{i + 1:05d}"
            names = []
            middle = self._middle(s)
            for k in range(r.randint(2, 4)):
                g, sn = self.render(s)
                n = f"{g} {middle} {sn}" if middle and k % 2 == 0 else f"{g} {sn}"
                if n not in names:
                    names.append(n)
            dobs, remarks = self._dob_field(s, lc)
            pob = None
            exposed = {"dob_full": [d for d in dobs if len(d) == 10], "dob_years": [d for d in dobs if len(d) == 4],
                       "pob_city": None}
            u = r.random()
            if u < lc["pob_field_share"]:
                pob = f"{s.pob_city}, {COUNTRY_NAMES[s.pob_country]}"
                exposed["pob_city"] = s.pob_city
            elif u < lc["pob_field_share"] + lc["pob_remarks_share"]:
                remarks.append(r.choice(REMARKS["pob"]).format(city=s.pob_city, country=COUNTRY_NAMES[s.pob_country]))
                exposed["pob_city"] = s.pob_city
            if not dobs and r.random() < 0.4:
                remarks.append(r.choice(REMARKS["dob"]).format(dob=_long_date(s.dob)))
                exposed["dob_full"] = [s.dob.isoformat()]
            remarks.append(r.choice(REMARKS["role"]).format(occupation=s.occupation))
            passports = [s.id_number] if r.random() < lc["passport_share"] else []
            entries.append({
                "id": entry_id, "source": r.choice(SOURCES), "program": r.choice(PROGRAMS[s.culture]),
                "type": "person", "names": names, "dobs": dobs, "pob": pob,
                "nationality": [s.nationality] if r.random() < lc["nationality_share"] else [],
                "passports": passports, "remarks": " ".join(remarks), "listed": "2019-01-01",
            })
            truth[entry_id] = s.id
            self.facts[entry_id] = exposed
        for i in range(lc["sanctioned_entities"]):
            culture = r.choices(cultures, weights)[0]
            country = r.choice(CULTURES[culture]["countries"] + ["AE", "CY"])
            co = self.new_company(country, r.choice(list(CULTURES[culture]["cities"].values())[0]))
            owner = self.new_subject(culture, 1950, 1990)
            co.owners = [owner.id]
            entry_id = f"SAN-E-{i + 1:05d}"
            names = list(dict.fromkeys([self.company_name(co), self.company_name(co, canonical=False)]))
            g, sn = self.render(owner, 1.0)
            remarks = [f"Registered in {COUNTRY_NAMES.get(country, country)}."]
            if r.random() < 0.6:
                remarks.append(f"Owned or controlled by {g} {sn}.")
            e = {
                "id": entry_id, "source": r.choice(SOURCES), "program": r.choice(PROGRAMS[culture]), "type": "entity",
                "names": names, "country": country if r.random() < 0.8 else None,
                "registration": [co.reg_number] if r.random() < 0.4 else [], "remarks": " ".join(remarks),
                "listed": "2020-06-01",
            }
            entries.append(e)
            truth[entry_id] = co.id
            self.facts[entry_id] = {"country": e["country"], "registration": e["registration"]}
        pc, pw = zip(*lc["pep_culture_weights"].items(), strict=True)
        for i in range(lc["peps"]):
            culture = r.choices(pc, pw)[0]
            s = self.new_subject(culture, 1945, 1990)
            entry_id = f"PEP-{i + 1:05d}"
            g, sn = self.render(s, 1.0)
            role = r.choice(REMARKS["pep_roles"])
            since = r.randint(2005, 2022)
            until = r.randint(since + 1, 2025) if r.random() < lc["pep_former_share"] else None
            dobs = [s.dob.isoformat()] if r.random() < 0.7 else [str(s.dob.year)]
            remarks = [f"{role}, {COUNTRY_NAMES[s.nationality]}, since {since}" + (f" until {until}." if until else ".")]
            exposed = {"dob_full": [d for d in dobs if len(d) == 10], "dob_years": [d for d in dobs if len(d) == 4],
                       "pob_city": None}
            if r.random() < 0.4:
                remarks.append(r.choice(REMARKS["pob"]).format(city=s.pob_city, country=COUNTRY_NAMES[s.pob_country]))
                exposed["pob_city"] = s.pob_city
            self.facts[entry_id] = exposed
            entries.append({
                "id": entry_id, "source": "PEP", "program": "PEP", "type": "person", "names": [f"{g} {sn}"],
                "dobs": dobs, "pob": None, "nationality": [s.nationality], "passports": [],
                "remarks": " ".join(remarks), "role": role, "pep_since": since, "pep_until": until,
                "listed": f"{since}-01-01",
            })
            truth[entry_id] = s.id
        return entries, truth

    def _middle(self, s: Subject) -> str:
        """Lists often carry a father's name or a patronymic that customers' records leave out."""
        r = self.rng
        if s.culture == "arabic" and r.random() < 0.6:
            return r.choice(sorted(CULTURES["arabic"]["given_m"]))
        if s.culture == "slavic" and r.random() < 0.6:
            father = r.choice(["Sergeevich", "Ivanovich", "Petrovich", "Nikolaevich", "Aleksandrovich"])
            return father if s.gender == "m" else father.replace("ich", "na")
        return ""

    def _dob_field(self, s: Subject, lc: dict) -> tuple[list[str], list[str]]:
        r = self.rng
        u = r.random()
        if u < lc["dob_full_share"]:
            dobs = [s.dob.isoformat()]
            if r.random() < lc["second_dob_share"]:
                dobs.append((s.dob + timedelta(days=r.choice([-365, 365, 31, -31]))).isoformat())
            return dobs, []
        if u < lc["dob_full_share"] + lc["dob_year_only_share"]:
            dobs = [str(s.dob.year)]
            if r.random() < lc["second_dob_share"]:
                dobs.append(str(s.dob.year + r.choice([-1, 1])))
            return dobs, []
        return [], []


def _long_date(d: date) -> str:
    return f"{d.day} {calendar.month_name[d.month]} {d.year}"


def month_dates(start: date, months: int) -> list[tuple[int, date, date]]:
    out = []
    y, m = start.year, start.month
    for k in range(months):
        first = date(y, m, 1)
        last = date(y, m, calendar.monthrange(y, m)[1])
        out.append((k + 1, first, last))
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def build(cfg: dict, out: Path) -> dict:
    w = World(cfg)
    r = w.rng
    entries, list_truth = w.make_lists()
    by_subject: dict[str, list[dict]] = {}
    for e in entries:
        by_subject.setdefault(list_truth[e["id"]], []).append(e)
    sanctioned = [list_truth[e["id"]] for e in entries if e["type"] == "person" and e["source"] != "PEP"]
    sanctioned_cos = [list_truth[e["id"]] for e in entries if e["type"] == "entity"]
    peps = [list_truth[e["id"]] for e in entries if e["source"] == "PEP"]
    provider = Provider(entries, cfg["screening"]["provider_threshold"])
    sanctioned_set = set(sanctioned)
    start = date.fromisoformat(cfg["world"]["start"])
    months = month_dates(start, cfg["world"]["history_months"] + cfg["world"]["heldout_months"])
    articles: list[dict] = []
    article_truth: dict[str, dict] = {}
    tenants_truth: dict[str, dict] = {}
    used_planted: set[str] = set()
    pending: dict[str, tuple] = {}

    def plant(pool: list[str], table: dict | None = None):
        free = [p for p in pool if p not in used_planted]
        if not free:
            return None
        sid = r.choice(free)
        used_planted.add(sid)
        return (table if table is not None else w.subjects)[sid]

    for t in cfg["tenants"]:
        tdir = out / "tenants" / t["id"]
        tdir.mkdir(parents=True, exist_ok=True)
        cultures, weights = zip(*t["culture_weights"].items(), strict=True)
        screenings, truth_rows = [], []
        for month, first, last in months:
            split = "heldout" if (t["heldout_tenant"] or month > cfg["world"]["history_months"]) else "history"
            for k in range(t["screenings_per_month"]):
                when = first + timedelta(days=r.randrange((last - first).days + 1))
                sid_ = f"{t['id']}-{month:02d}-{k + 1:04d}"
                parties = []  # (role, subject or company, kind)
                if t["segment"] == "individuals":
                    u = r.random()
                    subj = None
                    if u < t["planted_sanctioned"]:
                        subj = plant(sanctioned)
                    elif u < t["planted_sanctioned"] + t["planted_pep"]:
                        subj = plant(peps)
                    subj = subj or w.new_subject(r.choices(cultures, weights)[0])
                    parties.append(("customer", subj))
                else:
                    u = r.random()
                    if u < t["planted_sanctioned"] / 2:
                        co = plant(sanctioned_cos, w.companies) or w.new_company("DE", "Berlin")
                    else:
                        co = w.new_company(r.choice(["DE", "DE", "UK", "AE", "CY", "TR"]), r.choice(GERMAN_CITIES))
                    parties.append(("company", co))
                    for j in range(r.randint(1, 3)):
                        v = r.random()
                        subj = None
                        if v < t["planted_sanctioned"] / 2:
                            subj = plant(sanctioned)
                        elif v < t["planted_sanctioned"] / 2 + t["planted_pep"]:
                            subj = plant(peps)
                        subj = subj or w.new_subject(r.choices(cultures, weights)[0])
                        parties.append(("director" if j == 0 else "ubo", subj))
                record, names = export(t["export"], sid_, parties, w)
                alerts, party_truth = [], []
                for (role, p), pname in zip(parties, names, strict=True):
                    kind = "entity" if isinstance(p, Company) else "person"
                    for hit in provider.screen(pname, kind):
                        is_match = list_truth[hit["entry_id"]] == p.id
                        alerts.append({"alert_id": f"{sid_}-A{len(alerts) + 1}", "party_role": role,
                                       "party_name": pname, **hit})
                        party_truth.append({"alert_id": alerts[-1]["alert_id"], "is_match": is_match,
                                            "party_id": p.id, "entry_subject": list_truth[hit["entry_id"]]})
                    if kind == "person":
                        _media_for(w, p, pname, when, split, t, articles, article_truth, cfg, p.id in sanctioned_set)
                screenings.append({"screening_id": sid_, "month": month, "screened_on": when.isoformat(),
                                   "split": split, "record": record, "alerts": alerts})
                truth_rows.append({"screening_id": sid_, "split": split, "screened_on": when.isoformat(),
                                   "parties": [{"role": role, "id": p.id, "name": n,
                                                "kind": "entity" if isinstance(p, Company) else "person"}
                                               for (role, p), n in zip(parties, names, strict=True)],
                                   "alerts": party_truth})
        pending[t["id"]] = (tdir, screenings)
        (tdir / "dictionary.md").write_text(DICTIONARIES[t["export"]], encoding="utf-8")
        (tdir / "policy.md").write_text(POLICIES[t["id"]]["text"], encoding="utf-8")
        tenants_truth[t["id"]] = {"rows": truth_rows, "policy": POLICIES[t["id"]]["truth"]}

    media = MediaProvider(articles, cfg["screening"]["media_threshold"])
    by_article = {a["id"]: a for a in articles}
    subj_dicts = {k: {**asdict(v), "dob": v.dob.isoformat()} for k, v in w.subjects.items()}
    co_dicts = {k: asdict(v) for k, v in w.companies.items()}
    for tid, (tdir, screenings) in pending.items():
        policy = POLICIES[tid]["truth"]
        rows = {x["screening_id"]: x for x in tenants_truth[tid]["rows"]}
        for scr in screenings:
            row = rows[scr["screening_id"]]
            scr["media_hits"] = []
            row["media"] = []
            for party in row["parties"]:
                if party["kind"] != "person":
                    continue
                hits = media.search(party["name"], scr["screened_on"])
                scr["media_hits"] += [{"party_name": party["name"], **h} for h in hits]
                ideal, found = media_ideal(party["id"], hits, by_article, article_truth, scr["screened_on"], policy)
                row["media"].append({"party_name": party["name"], "party_id": party["id"], "ideal": ideal,
                                     "findings": found, "hits": [h["article_id"] for h in hits]})
            alert_entries = {a["alert_id"]: a["entry_id"] for a in scr["alerts"]}
            for a in row["alerts"]:
                facts = w.facts[alert_entries[a["alert_id"]]]
                pid = a["party_id"]
                conflicts = (entity_conflicts(co_dicts[pid], facts) if pid in co_dicts
                             else person_conflicts(subj_dicts[pid], facts))
                a["conflicts"] = conflicts
                a["ideal"] = alert_ideal(a["is_match"], conflicts, policy)
        _write_jsonl(tdir / "screenings.jsonl", screenings)

    (out / "lists").mkdir(parents=True, exist_ok=True)
    _write_jsonl(out / "lists" / "entries.jsonl", entries)
    (out / "media").mkdir(parents=True, exist_ok=True)
    articles.sort(key=lambda a: a["id"])
    _write_jsonl(out / "media" / "articles.jsonl", articles)
    truth_dir = out / "truth"
    truth_dir.mkdir(parents=True, exist_ok=True)
    (truth_dir / "world.json").write_text(json.dumps(
        {"subjects": subj_dicts, "companies": co_dicts, "list_truth": list_truth, "list_facts": w.facts,
         "articles": article_truth},
        ensure_ascii=False) + "\n", encoding="utf-8")
    for tid, tt in tenants_truth.items():
        (truth_dir / f"{tid}.json").write_text(json.dumps(tt, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"entries": len(entries), "articles": len(articles),
            "screenings": {t: len(v["rows"]) for t, v in tenants_truth.items()},
            "alerts": {t: sum(len(x["alerts"]) for x in v["rows"]) for t, v in tenants_truth.items()},
            "matches": {t: sum(a["is_match"] for x in v["rows"] for a in x["alerts"]) for t, v in tenants_truth.items()}}


def _media_for(w: World, s: Subject, printed: str, when: date, split: str, t: dict, articles: list, truth: dict,
               cfg: dict, listed: bool) -> None:
    """Articles that a media search for this person could return: about them, or about namesakes."""
    r, mc = w.rng, cfg["media"]
    family = "heldout" if split == "heldout" else "dev"
    lang = "de" if t["id"] == "kreditwerk" or r.random() < 0.3 else "en"
    planned: list[tuple[Subject, bool, str]] = []
    if listed and r.random() < 0.7:
        planned.append((s, True, "sanctions_evasion"))
    elif r.random() < mc["adverse_customer_share"]:
        planned.append((s, True, r.choice(TOPICS_ADVERSE)))
    if r.random() < 0.08:
        planned.append((s, False, r.choice(TOPICS_NEUTRAL)))
    for _ in range(r.randint(*mc["namesake_articles_per_name"]) if r.random() < 0.35 else 0):
        other = w.namesake(s)
        adverse = r.random() < 0.6
        planned.append((other, adverse, r.choice(TOPICS_ADVERSE if adverse else TOPICS_NEUTRAL)))
    for subj, adverse, topic in planned:
        published = when - timedelta(days=r.randrange(1, 365 * mc["years_back"]))
        detailed = r.random() < mc["identifying_detail_share"]
        outcome = None
        if adverse:
            outcome = "acquitted" if r.random() < mc["acquitted_share"] else r.choice(["charged", "convicted",
                                                                                         "investigated"])
        g, sn = w.render(subj, 0.7) if subj.id != s.id else (printed.split(" ", 1) + [""])[:2]
        name = f"{g} {sn}".strip()
        age = subj.age_at(published)
        key = "adverse" if adverse else "neutral"
        tpl = r.choice(ARTICLE[lang][key][topic if adverse else "any"])
        detail = r.choice(ARTICLE[lang]["detail"]).format(age=age, city=subj.residence_city,
                                                          occupation=subj.occupation) if detailed else ""
        if not detailed:
            tpl = tpl.replace(", {detail}", "")
        body = tpl.format(name=name, detail=detail, topic=topic, outcome=ARTICLE[lang]["outcome"].get(outcome, ""))
        injected = None
        if adverse and subj.id == s.id and r.random() < mc["injection_share"] * 4:
            injected = r.choice(INJECTIONS[family])
            body = f"{body} {injected['text']}"
        aid = f"ART-{len(articles) + 1:06d}"
        articles.append({"id": aid, "published": published.isoformat(), "outlet": r.choice(ARTICLE[lang]["outlets"]),
                         "lang": lang, "persons": [name], "title": body.split(".")[0][:90], "body": body})
        truth[aid] = {"subject": subj.id, "adverse": adverse, "topic": topic, "outcome": outcome,
                      "identifying": detailed, "injection": injected, "family": family}


def export(fmt: str, sid: str, parties: list, w: World) -> tuple[dict, list[str]]:
    """The screening record in the customer's own export format, and the names the provider screened."""
    names = []
    people = []
    for role, p in parties:
        if isinstance(p, Company):
            names.append(w.company_name(p, canonical=w.rng.random() < 0.6))
            continue
        g, sn = w.render(p)
        names.append(f"{g} {sn}")
        people.append((role, p, g, sn))
    if fmt == "finvia_json":
        role, p, g, sn = people[0]
        return {"customer_id": sid, "first_name": g, "last_name": sn, "birth_date": p.dob.isoformat(),
                "nationality": p.nationality, "birth_place": p.pob_city, "residence": f"{p.residence_city}, DE",
                "occupation": p.occupation}, names
    if fmt == "northbank_fixed":
        role, p, g, sn = people[0]
        return {"ref": sid, "name": f"{sn.upper()}/{g.upper()}", "dob": p.dob.strftime("%Y%m%d"),
                "cob": COUNTRY_NAMES[p.pob_country], "pob": p.pob_city, "nat": ISO3[p.nationality],
                "addr": f"{p.residence_city}"}, names
    co = parties[0][1]
    if fmt == "ledgerly_csv":
        return {"entity_id": sid, "legal_name": names[0], "reg_no": co.reg_number, "country": co.country,
                "parties": [{"role": role, "full_name": f"{g} {sn}".upper(), "dob": p.dob.strftime("%m/%d/%Y"),
                             "country_of_birth": COUNTRY_NAMES[p.pob_country], "city_of_birth": p.pob_city,
                             "nationality": p.nationality} for role, p, g, sn in people]}, names
    return {"kunden_nr": sid, "firma": names[0], "handelsregister": co.reg_number, "sitz": co.city,
            "land": co.country,
            "beteiligte": [{"rolle": "Geschäftsführer" if role == "director" else "wirtschaftlich Berechtigter",
                            "vorname": g, "nachname": sn, "geburtsdatum": p.dob.strftime("%d.%m.%Y"),
                            "geburtsort": p.pob_city, "staatsangehoerigkeit": NATIONALITY_DE[p.nationality]}
                           for role, p, g, sn in people]}, names


ISO3 = {"SY": "SYR", "IQ": "IRQ", "LB": "LBN", "AE": "ARE", "EG": "EGY", "JO": "JOR", "RU": "RUS", "UA": "UKR",
        "BY": "BLR", "KZ": "KAZ", "DE": "DEU", "AT": "AUT", "CH": "CHE", "RO": "ROU", "MD": "MDA", "TR": "TUR",
        "ES": "ESP", "MX": "MEX", "VE": "VEN", "CO": "COL", "UK": "GBR", "CY": "CYP"}

DICTIONARIES = {
    "finvia_json": "# Finvia export\n\nOne JSON object per screened customer (private individuals).\n\n"
                   "| field | meaning |\n|---|---|\n| customer_id | screening id |\n| first_name, last_name | as on the ID |\n"
                   "| birth_date | ISO 8601, YYYY-MM-DD |\n| nationality | ISO 3166-1 alpha-2 |\n"
                   "| birth_place | city of birth |\n| residence | city, country |\n| occupation | free text |\n",
    "ledgerly_csv": "# Ledgerly export\n\nOne record per business customer, with its people under `parties`.\n"
                    "Ledgerly's onboarding runs on its US parent's stack.\n\n| field | meaning |\n|---|---|\n"
                    "| entity_id | screening id |\n| legal_name | registered name |\n| reg_no | registration number |\n"
                    "| country | country of registration, ISO alpha-2 |\n| parties[].role | director or ubo |\n"
                    "| parties[].full_name | GIVEN SURNAME, upper case |\n| parties[].dob | MM/DD/YYYY |\n"
                    "| parties[].country_of_birth | English country name |\n| parties[].city_of_birth | city |\n"
                    "| parties[].nationality | ISO alpha-2 |\n",
    "kreditwerk_de": "# Kreditwerk Export\n\nEin Datensatz je Firmenkunde, Beteiligte unter `beteiligte`.\n\n"
                     "| Feld | Bedeutung |\n|---|---|\n| kunden_nr | Prüfnummer |\n| firma | Firmenname |\n"
                     "| handelsregister | HRB-Nummer |\n| sitz | Sitz |\n| land | Land (ISO alpha-2) |\n"
                     "| beteiligte[].rolle | Geschäftsführer oder wirtschaftlich Berechtigter |\n"
                     "| beteiligte[].vorname, nachname | Name |\n| beteiligte[].geburtsdatum | TT.MM.JJJJ |\n"
                     "| beteiligte[].geburtsort | Geburtsort |\n"
                     "| beteiligte[].staatsangehoerigkeit | Adjektiv, z. B. deutsch, türkisch |\n",
    "northbank_fixed": "# Northbank export\n\nOne record per private customer, from the core banking system.\n\n"
                       "| field | meaning |\n|---|---|\n| ref | screening id |\n| name | SURNAME/GIVEN, upper case |\n"
                       "| dob | YYYYMMDD |\n| cob | country of birth, English name |\n| pob | city of birth |\n"
                       "| nat | nationality, ISO 3166-1 alpha-3 |\n| addr | city of residence |\n",
}


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
