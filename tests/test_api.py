from fastapi.testclient import TestClient

from fat.api import create_app

from .test_template import Fixed, person_entry, screening, template


def test_screen_queue_decide_metrics(rt):
    tpl = template(rt, "finvia", Fixed({}))
    tpl.lists.entries["T-1"] = person_entry(dobs=["1971-02-03"])
    tpl.lists.entries["T-2"] = person_entry(id="T-2")
    app = create_app(lambda tenant: tpl if tenant == "finvia" else None)
    c = TestClient(app)
    s = screening()
    s["alerts"].append(s["alerts"][0] | {"alert_id": "a2", "entry_id": "T-2"})
    r = c.post("/v1/tenants/finvia/screenings", json=s)
    assert r.status_code == 200
    assert [a["disposition"] for a in r.json()["alerts"]] == ["clear", "escalate"]
    q = c.get("/v1/tenants/finvia/queue").json()
    assert [x["alert_id"] for x in q] == ["a2"]
    assert c.post("/v1/cases/a2/decision", json={"analyst": "k.weiss", "decision": "false_positive"}).status_code == 200
    assert c.get("/v1/tenants/finvia/queue").json() == []
    m = c.get("/v1/tenants/finvia/metrics").json()
    assert (m["alerts"], m["closed_by_agent"], m["analysts_closed"], m["open_cases"]) == (2, 1, 1, 0)
    assert c.post("/v1/tenants/nobody/screenings", json=s).status_code == 404
    assert c.post("/v1/cases/zz/decision", json={"analyst": "a", "decision": "true_match"}).status_code == 404
