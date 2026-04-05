import sqlite3
from datetime import datetime
from pathlib import Path

from .models import Entry, Session

DB_PATH = Path.home() / ".maflow" / "auditor.db"


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id          TEXT PRIMARY KEY,
                date        TEXT NOT NULL,
                role        TEXT NOT NULL,
                model       TEXT NOT NULL,
                provider    TEXT NOT NULL,
                done        TEXT,
                in_progress TEXT,
                pending     TEXT,
                blocked     TEXT,
                next_task   TEXT,
                turn_count  INTEGER DEFAULT 0,
                drift_ratio REAL DEFAULT 0.0,
                alert_level TEXT DEFAULT 'green',
                created_at  TEXT NOT NULL,
                raw         TEXT
            )
        """)
        conn.commit()


def session_exists(session_id: str) -> bool:
    """Check if session already stored."""
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return row is not None


def save_session(session: Session) -> None:
    """Insert session if not already stored."""
    if session_exists(session.id):
        return
    e = session.entry
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions
            (id, date, role, model, provider, done, in_progress,
             pending, blocked, next_task, turn_count, drift_ratio,
             alert_level, created_at, raw)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
            (
                session.id,
                e.date,
                e.role,
                e.model,
                e.provider,
                e.done,
                e.in_progress,
                e.pending,
                e.blocked,
                e.next_task,
                session.turn_count,
                session.drift_ratio,
                session.alert_level,
                session.created_at.isoformat(),
                e.raw,
            ),
        )
        conn.commit()


def load_all_sessions() -> list[Session]:
    """Load all sessions ordered by date."""
    with _get_connection() as conn:
        rows = conn.execute("SELECT * FROM sessions ORDER BY created_at ASC").fetchall()
    return [_row_to_session(r) for r in rows]


def load_worst_sessions(limit: int = 5) -> list[Session]:
    """Return sessions with highest drift ratio."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY drift_ratio DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_session(r) for r in rows]


def _row_to_session(row: sqlite3.Row) -> Session:
    entry = Entry(
        date=row["date"],
        role=row["role"],
        model=row["model"],
        provider=row["provider"],
        done=row["done"] or "",
        in_progress=row["in_progress"] or "",
        pending=row["pending"] or "",
        blocked=row["blocked"] or "",
        next_task=row["next_task"] or "",
        raw=row["raw"] or "",
    )
    return Session(
        id=row["id"],
        entry=entry,
        turn_count=row["turn_count"],
        drift_ratio=row["drift_ratio"],
        alert_level=row["alert_level"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
