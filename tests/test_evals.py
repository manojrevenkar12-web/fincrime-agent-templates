from fat import lock
from fat.evals.pipeline import gate


def test_heldout_pin_holds():
    assert lock.changed() == []


def test_gate_names_what_fails(rt):
    m = {
        "matches_cleared": 1,
        "policy_breaches": 0,
        "obeyed": 0,
        "missed_findings": 0,
        "auto_clear_ci": [0.5, 0.6],
        "wrong_person": 0,
        "media_parties": 100,
    }
    g = gate(m, rt)
    assert not g["ship"] and g["failed"] == ["true matches closed without review"]
    assert gate(m | {"matches_cleared": 0}, rt)["ship"]
