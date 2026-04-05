import re
from pathlib import Path

from .models import Entry

ROLE_PROVIDER_MAP = {
    "sonnet": "claude",
    "opus": "claude",
    "haiku": "claude",
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

ENTRY_LIKE_PATTERN = re.compile(
    r"\[[^\]]+\]\[[^\]]+\]",
    re.MULTILINE,
)


def _extract_model(role_field: str) -> str:
    parts = re.split(r"[·\-\s]", role_field.lower())
    for part in reversed(parts):
        part = part.strip()
        if part in ROLE_PROVIDER_MAP:
            return part
    return "unknown"


def _extract_role(role_field: str) -> str:
    parts = re.split(r"[·\-]", role_field)
    return parts[0].strip() if parts else role_field.strip()


def _extract_provider(model: str) -> str:
    if model in ("maflow", "unknown"):
        return "auditor"
    provider = ROLE_PROVIDER_MAP.get(model.lower(), "unknown")
    if provider == "unknown":
        import warnings

        warnings.warn(
            f"Unknown model '{model}' — provider set to 'unknown'. Add to ROLE_PROVIDER_MAP if needed."
        )
    return provider


def parse_log(log_path: str | Path) -> list[Entry]:
    """
    Parse agent-log.md and return list of Entry objects.

    Raises:
        FileNotFoundError: If log file does not exist.
    """
    path = Path(log_path)
    if not path.exists():
        raise FileNotFoundError(f"agent-log.md not found at: {path}")

    content = path.read_text(encoding="utf-8")
    entries = []

    matched = list(ENTRY_PATTERN.finditer(content))
    like_count = len(ENTRY_LIKE_PATTERN.findall(content))

    if like_count > len(matched):
        import warnings

        warnings.warn(
            f"{like_count - len(matched)} entry-like block(s) found but failed to parse. "
            "Check for missing emoji or wrong format in agent-log.md."
        )

    for match in matched:
        role_field = match.group("role")
        model = _extract_model(role_field)
        role = _extract_role(role_field)
        provider = _extract_provider(model)

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
            raw=match.group(0),
        )
        entries.append(entry)

    return entries


def parse_last_entry(log_path: str | Path) -> Entry | None:
    entries = parse_log(log_path)
    return entries[-1] if entries else None


def parse_last_non_auditor_entry(log_path: str | Path) -> Entry | None:
    """Return last entry that is not from the Auditor."""
    entries = parse_log(log_path)
    for entry in reversed(entries):
        if entry.role.lower() != "auditor":
            return entry
    return None
