from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from .models import Session
from .tracker import get_summary

console = Console()

PROVIDER_COLORS = {
    "claude": "dark_orange",
    "gemini": "steel_blue1",
}

ALERT_COLORS = {
    "green": "green",
    "yellow": "yellow",
    "red": "red",
}

ALERT_ICONS = {
    "green": "●",
    "yellow": "●",
    "red": "●",
}


def _provider_text(session: Session) -> Text:
    provider = session.entry.provider
    model = session.entry.model
    color = PROVIDER_COLORS.get(provider, "white")
    return Text(f"{provider}/{model}", style=color)


def _drift_text(session: Session) -> Text:
    drift = session.drift_ratio
    level = session.alert_level
    color = ALERT_COLORS[level]
    icon = ALERT_ICONS[level]
    return Text(f"{icon} {drift}x", style=color)


def _role_text(session: Session) -> Text:
    role = session.entry.role
    provider = session.entry.provider
    color = PROVIDER_COLORS.get(provider, "white")
    return Text(role, style=color)


def print_report(sessions: list[Session]) -> None:
    """Print full audit report with colored table."""
    if not sessions:
        console.print("[dim]No sessions found in agent-log.md[/dim]")
        return

    summary = get_summary(sessions)
    _print_summary(summary, sessions)
    _print_table(sessions)
    _print_worst(summary)


def _print_summary(summary: dict, sessions: list[Session]) -> None:
    claude_count = summary["claude_sessions"]
    gemini_count = summary["gemini_sessions"]
    red_count = summary["red_alerts"]

    console.print()
    console.print("[bold]maflow audit report[/bold]")
    console.print(
        f"[dim]{summary['total_sessions']} sessions · "
        f"[dark_orange]{claude_count} Claude[/dark_orange] · "
        f"[steel_blue1]{gemini_count} Gemini[/steel_blue1] · "
        f"[red]{red_count} red alerts[/red][/dim]"
    )
    console.print()


def _print_table(sessions: list[Session]) -> None:
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim")
    table.add_column("Date", style="dim", width=12)
    table.add_column("Role", width=14)
    table.add_column("Model", width=20)
    table.add_column("Turns", justify="right", width=7)
    table.add_column("Drift", justify="right", width=10)
    table.add_column("Next task", width=40)

    for s in sessions:
        next_task = s.entry.next_task
        if len(next_task) > 38:
            next_task = next_task[:35] + "..."

        table.add_row(
            s.entry.date[:10],
            _role_text(s),
            _provider_text(s),
            str(s.turn_count),
            _drift_text(s),
            Text(next_task, style="dim"),
        )

    console.print(table)


def _print_worst(summary: dict) -> None:
    worst = summary.get("worst")
    if not worst or worst.alert_level == "green":
        return
    console.print(
        f"[bold red]Worst session:[/bold red] "
        f"{worst.entry.role}·{worst.entry.model} — "
        f"drift {worst.drift_ratio}x · "
        f"rotate when drift > 4.0"
    )
    console.print()


def print_worst(sessions: list[Session], limit: int = 5) -> None:
    """Print only the worst sessions by drift ratio."""
    sorted_sessions = sorted(sessions, key=lambda s: s.drift_ratio, reverse=True)
    worst = sorted_sessions[:limit]
    console.print()
    console.print(f"[bold]Top {limit} sessions by drift[/bold]")
    console.print()
    _print_table(worst)
