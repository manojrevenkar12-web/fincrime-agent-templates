"""Cases and decisions in SQL. Every agent decision is stored with its reasons; analysts' decisions are stored
next to it, so agreement and queue sizes are queries, not spreadsheets."""

from __future__ import annotations

import json
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS screenings (
  screening_id TEXT PRIMARY KEY, tenant TEXT NOT NULL, screened_on TEXT NOT NULL,
  latency_ms REAL, cost_eur REAL, issues TEXT
);
CREATE TABLE IF NOT EXISTS alerts (
  alert_id TEXT PRIMARY KEY, screening_id TEXT NOT NULL REFERENCES screenings(screening_id), tenant TEXT NOT NULL,
  entry_id TEXT, list TEXT, party_name TEXT, disposition TEXT NOT NULL, clear_score REAL, conflicts TEXT,
  reasons TEXT
);
CREATE TABLE IF NOT EXISTS media (
  screening_id TEXT NOT NULL REFERENCES screenings(screening_id), tenant TEXT NOT NULL, party_name TEXT NOT NULL,
  disposition TEXT NOT NULL, findings TEXT, unsure TEXT, PRIMARY KEY (screening_id, party_name)
);
CREATE TABLE IF NOT EXISTS decisions (
  case_id TEXT NOT NULL, kind TEXT NOT NULL, analyst TEXT NOT NULL, decision TEXT NOT NULL, note TEXT,
  decided_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (case_id, kind)
);
"""

METRICS = """
SELECT
  COUNT(*)                                                         AS alerts,
  SUM(disposition = 'clear')                                       AS closed_by_agent,
  SUM(disposition != 'clear')                                      AS sent_to_analysts,
  SUM(disposition = 'likely_match')                                AS likely_matches,
  SUM(disposition != 'clear' AND d.decision IS NULL)               AS open_cases,
  SUM(d.decision = 'false_positive')                               AS analysts_closed,
  SUM(d.decision = 'true_match')                                   AS analysts_confirmed
FROM alerts a LEFT JOIN decisions d ON d.case_id = a.alert_id AND d.kind = 'alert'
WHERE a.tenant = ?
"""


class Store:
    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def save(self, tenant: str, screened_on: str, review) -> None:
        with self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO screenings VALUES (?,?,?,?,?,?)",
                (
                    review.screening_id,
                    tenant,
                    screened_on,
                    review.latency_ms,
                    review.cost_eur,
                    json.dumps(review.issues),
                ),
            )
            for a in review.alerts:
                self.db.execute(
                    "INSERT OR REPLACE INTO alerts VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (
                        a.alert_id,
                        review.screening_id,
                        tenant,
                        a.entry_id,
                        a.list,
                        a.party_name,
                        a.disposition,
                        a.clear_score,
                        json.dumps(a.conflicts),
                        json.dumps(a.reasons),
                    ),
                )
            for m in review.media:
                self.db.execute(
                    "INSERT OR REPLACE INTO media VALUES (?,?,?,?,?,?)",
                    (
                        review.screening_id,
                        tenant,
                        m.party_name,
                        m.disposition,
                        json.dumps(m.findings),
                        json.dumps(m.unsure),
                    ),
                )

    def queue(self, tenant: str) -> list[dict]:
        rows = self.db.execute(
            "SELECT a.* FROM alerts a LEFT JOIN decisions d ON d.case_id = a.alert_id AND d.kind = 'alert' "
            "WHERE a.tenant = ? AND a.disposition != 'clear' AND d.decision IS NULL "
            "ORDER BY a.disposition = 'likely_match' DESC, a.alert_id",
            (tenant,),
        ).fetchall()
        return [dict(r) | {"conflicts": json.loads(r["conflicts"]), "reasons": json.loads(r["reasons"])} for r in rows]

    def decide(self, case_id: str, kind: str, analyst: str, decision: str, note: str | None) -> None:
        with self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO decisions (case_id, kind, analyst, decision, note) VALUES (?,?,?,?,?)",
                (case_id, kind, analyst, decision, note),
            )

    def exists(self, case_id: str) -> bool:
        return self.db.execute("SELECT 1 FROM alerts WHERE alert_id = ?", (case_id,)).fetchone() is not None

    def metrics(self, tenant: str) -> dict:
        row = dict(self.db.execute(METRICS, (tenant,)).fetchone())
        row = {k: v or 0 for k, v in row.items()}
        row["closed_by_agent_share"] = round(row["closed_by_agent"] / row["alerts"], 4) if row["alerts"] else 0.0
        media = self.db.execute(
            "SELECT disposition, COUNT(*) n FROM media WHERE tenant = ? GROUP BY disposition", (tenant,)
        ).fetchall()
        row["media"] = {r["disposition"]: r["n"] for r in media}
        return row
