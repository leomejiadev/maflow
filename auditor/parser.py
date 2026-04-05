import re
from pathlib import Path

from .models import Entry

ROLE_PROVIDER_MAP = {
    "sonnet": "claude",
    "opus": "claude",
    "flash": "gemini",
    "pro": "gemini",
}

ENTRY_PATTERN = re.compile(
    r"\[(?P<date>[^\]]+)\]\[(?P<role>[^\]]+)\]\s*\n"
    r"✅\s*DONE:\s*(?P<done>[^\n]+)\n"
    r"⏳\s*IN PROGRESS:\s*(?P<in_progress>[^\n]+)\n"
    r"❌\s*PENDING:\s*(?P<pending>[^\n]+)\n"
    r"🚫\s*BLOCKED:\s*(?P<blocked>[^\n]+)\n"
    r"➡️\s*NEXT:\s*(?P<next_task>[^\n]+)",
    re.MULTILINE,
)


def _extract_model(role_field: str) -> str:
    """Extract model name from role field like 'Worker·Flash'."""
    parts = re.split(r"[·\-\s]", role_field.lower())
    for part in reversed(parts):
        part = part.strip()
        if part in ROLE_PROVIDER_MAP:
            return part
    return "unknown"


def _extract_role(role_field: str) -> str:
    """Extract clean role name from role field like 'Worker·Flash'."""
    parts = re.split(r"[·\-]", role_field)
    return parts[0].strip() if parts else role_field.strip()


def _extract_provider(model: str) -> str:
    return ROLE_PROVIDER_MAP.get(model.lower(), "unknown")


def parse_log(log_path: str | Path) -> list[Entry]:
    """
    Parse agent-log.md and return list of Entry objects.

    Args:
        log_path: Path to agent-log.md file.

    Returns:
        List of Entry objects ordered by appearance in file.

    Raises:
        FileNotFoundError: If log file does not exist.
    """
    path = Path(log_path)
    if not path.exists():
        raise FileNotFoundError(f"agent-log.md not found at: {path}")

    content = path.read_text(encoding="utf-8")
    entries = []

    for match in ENTRY_PATTERN.finditer(content):
        role_field = match.group("role")
        model = _extract_model(role_field)
        role = _extract_role(role_field)
        provider = _extract_provider(model)
        raw = match.group(0)

        entry = Entry(
            date=match.group("date").strip(),
            role=role,
            model=model,
            provider=provider,
            done=match.group("done").strip(),
            in_progress=match.group("in_progress").strip(),
            pending=match.group("pending").strip(),
            blocked=match.group("blocked").strip(),
            next_task=match.group("next_task").strip(),
            raw=raw,
        )
        entries.append(entry)

    return entries


def parse_last_entry(log_path: str | Path) -> Entry | None:
    """
    Return only the last entry from agent-log.md.
    Agents use this to resume without reading full history.

    Args:
        log_path: Path to agent-log.md file.

    Returns:
        Last Entry or None if no entries found.
    """
    entries = parse_log(log_path)
    return entries[-1] if entries else None
