from datetime import date

from fat.agent.mapping import Mapping, party_for

from .conftest import history


def mapping(tenant, rt):
    from fat import settings

    return Mapping(settings.customer(tenant), rt["activation"]["date_formats"])


def test_each_customer_export_parses_to_parties_with_dates(rt):
    for tenant in ("finvia", "ledgerly", "kreditwerk", "northbank"):
        m = mapping(tenant, rt)
        for s in history(tenant, 30):
            p = m.parse(s["record"])
            assert not p.issues, (tenant, p.issues)
            people = [x for x in p.parties if x.kind == "person"]
            assert people and all(isinstance(x.dob, date) for x in people)
            for a in s["alerts"]:
                assert party_for(p, a["party_name"]) is not None


def test_ledgerly_dates_are_month_first_and_auto_mode_gets_them_wrong(rt):
    explicit, auto = mapping("ledgerly", rt), mapping("_generic", rt)
    rec = {
        "entity_id": "x",
        "legal_name": "A Ltd",
        "reg_no": "1",
        "country": "UK",
        "parties": [
            {
                "role": "director",
                "full_name": "JAN WEBER",
                "dob": "03/07/1984",
                "country_of_birth": "Germany",
                "city_of_birth": "Berlin",
                "nationality": "DE",
            }
        ],
    }
    assert explicit.parse(rec).parties[1].dob == date(1984, 3, 7)
    assert auto.parse(rec).parties[1].dob == date(1984, 7, 3)  # the silent error an activation must catch


def test_german_nationality_adjectives_and_surname_first_names(rt):
    k = mapping("kreditwerk", rt).parse(history("kreditwerk", 1)[0]["record"])
    assert all(p.nationality and len(p.nationality) == 2 for p in k.parties if p.kind == "person")
    nb = mapping("northbank", rt).parse(
        {
            "ref": "r",
            "name": "IVANOV/SERGEI",
            "dob": "19700102",
            "cob": "Russia",
            "pob": "Moscow",
            "nat": "RUS",
            "addr": "Berlin",
        }
    )
    p = nb.parties[0]
    assert (p.name, p.dob, p.nationality, p.residence_city) == ("Sergei Ivanov", date(1970, 1, 2), "RU", "Berlin")
