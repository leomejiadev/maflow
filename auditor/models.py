from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Entry:
    """Single agent session entry from agent-log.md."""

    date: str
    role: str
    model: str
    provider: str  # claude | gemini
    done: str
    in_progress: str
    pending: str
    blocked: str
    next_task: str
    raw: str  # original text for debugging


@dataclass
class Session:
    """Parsed and enriched session with metrics."""

    id: str
    entry: Entry
    turn_count: int = 0
    drift_ratio: float = 0.0
    alert_level: str = "green"  # green | yellow | red
    created_at: datetime = field(default_factory=datetime.now)
