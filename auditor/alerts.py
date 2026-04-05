from .models import Session

MESSAGES = {
    "green": "Session healthy.",
    "yellow": "Session growing. Consider rotating soon.",
    "red": "Session too long. Rotate now — say 'Session complete.'",
}

COLORS = {
    "green": "green",
    "yellow": "yellow",
    "red": "red",
}


def get_alert(session: Session) -> dict:
    """
    Return alert info for a session.

    Returns:
        Dict with level, color, message and drift.
    """
    level = session.alert_level
    return {
        "level": level,
        "color": COLORS[level],
        "message": MESSAGES[level],
        "drift": session.drift_ratio,
        "role": session.entry.role,
        "model": session.entry.model,
    }


def should_rotate(session: Session) -> bool:
    """Return True if session should be rotated immediately."""
    return session.alert_level == "red"


def print_alert(session: Session) -> None:
    """Print alert to stdout if session needs attention."""
    if session.alert_level == "green":
        return
    alert = get_alert(session)
    prefix = "⚠️ " if alert["level"] == "yellow" else "🔴 "
    print(
        f"{prefix}{alert['role']}·{alert['model']} — {alert['message']} (drift {alert['drift']}x)"
    )
