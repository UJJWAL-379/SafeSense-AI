import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "safesense.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS reports (
            report_id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            signal_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_id TEXT NOT NULL,
            decision TEXT NOT NULL,
            comment TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)


def save_signal(report_id: str, text: str, signal: Any) -> None:
    with _connect() as conn:
        conn.execute("INSERT OR REPLACE INTO reports(report_id,text,signal_json) VALUES(?,?,?)", (report_id, text, signal.model_dump_json()))


def save_feedback(cluster_id: str, decision: str, comment: str = "") -> None:
    if decision not in {"confirmed", "rejected"}:
        raise ValueError("decision must be confirmed or rejected")
    with _connect() as conn:
        conn.execute("INSERT INTO feedback(cluster_id,decision,comment) VALUES(?,?,?)", (cluster_id, decision, comment))


def feedback_summary() -> dict[str, int]:
    with _connect() as conn:
        rows = conn.execute("SELECT decision, COUNT(*) AS n FROM feedback GROUP BY decision").fetchall()
    return {row["decision"]: row["n"] for row in rows}
