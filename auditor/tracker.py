import hashlib

from .database import init_db, save_session
from .models import Entry, Session

ALERT_THRESHOLDS = {
    "green": (0.0, 2.0),
    "yellow": (2.0, 4.0),
    "red": (4.0, float("inf")),
}

BASELINE_TURNS = {
    "architect": 2,
    "worker": 4,
    "refactor": 2,
    "evaluator": 1,
}


def _session_id(entry: Entry) -> str:
    """Generate stable ID from entry content."""
    raw = f"{entry.date}{entry.role}{entry.model}{entry.done}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _calc_turn_count(entries: list[Entry], current: Entry) -> int:
    """
    Count consecutive entries of the same role+model before a role change.
    Simulates turns within a logical session.
    """
    role = current.role.lower()
    count = 0
    for e in reversed(entries):
        if e.role.lower() == role and e.model.lower() == current.model.lower():
            count += 1
        else:
            break
    return max(count, 1)


def _calc_drift(role: str, turn_count: int) -> float:
    """
    Calculate drift ratio: actual turns / expected baseline.
    Higher = more token drift.
    """
    baseline = BASELINE_TURNS.get(role.lower(), 2)
    return round(turn_count / baseline, 2)


def _alert_level(drift: float) -> str:
    for level, (low, high) in ALERT_THRESHOLDS.items():
        if low <= drift < high:
            return level
    return "red"


def process_entries(entries: list[Entry]) -> list[Session]:
    """
    Convert Entry list into Session list with metrics.
    Saves new sessions to SQLite automatically.

    Args:
        entries: Parsed entries from agent-log.md

    Returns:
        List of Session objects with drift and alert data.
    """
    init_db()
    sessions = []

    for i, entry in enumerate(entries):
        prior = entries[:i]
        turn_count = _calc_turn_count(prior + [entry], entry)
        drift = _calc_drift(entry.role, turn_count)
        alert = _alert_level(drift)

        session = Session(
            id=_session_id(entry),
            entry=entry,
            turn_count=turn_count,
            drift_ratio=drift,
            alert_level=alert,
        )
        save_session(session)
        sessions.append(session)

    return sessions


def get_summary(sessions: list[Session]) -> dict:
    """
    Generate summary metrics across all sessions.

    Returns:
        Dict with total, by_provider counts and worst session.
    """
    claude = [s for s in sessions if s.entry.provider == "claude"]
    gemini = [s for s in sessions if s.entry.provider == "gemini"]
    red = [s for s in sessions if s.alert_level == "red"]
    worst = max(sessions, key=lambda s: s.drift_ratio) if sessions else None

    return {
        "total_sessions": len(sessions),
        "claude_sessions": len(claude),
        "gemini_sessions": len(gemini),
        "red_alerts": len(red),
        "worst": worst,
    }
