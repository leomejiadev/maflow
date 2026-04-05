from datetime import date
from pathlib import Path

from .models import Session
from .tracker import get_summary


def _build_entry(sessions: list[Session]) -> str:
    """Build close protocol entry for auditor run."""
    summary = get_summary(sessions)
    total = summary["total_sessions"]
    red = summary["red_alerts"]
    worst = summary["worst"]

    if red > 0 and worst:
        next_task = f"rotate session — {worst.entry.role}·{worst.entry.model} at {worst.drift_ratio}x drift"
    else:
        next_task = "no alerts — continue workflow"

    today = date.today().isoformat()
    return (
        f"\n[{today}][Auditor·maflow]\n"
        f"✅ DONE: audit report — {total} sessions analyzed\n"
        f"⏳ IN PROGRESS: N/A\n"
        f"❌ PENDING: N/A\n"
        f"🚫 BLOCKED: N/A\n"
        f"➡️ NEXT: {next_task}\n"
    )


def write_audit_entry(log_path: str | Path, sessions: list[Session]) -> None:
    """
    Append auditor entry to agent-log.md after a report run.

    Args:
        log_path: Path to agent-log.md
        sessions: Sessions from latest audit run
    """
    path = Path(log_path)
    if not path.exists():
        return

    entry = _build_entry(sessions)
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry)
