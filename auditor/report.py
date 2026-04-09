from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .models import Session
from .tracker import get_summary

console = Console()

PROVIDER_COLORS = {
    "claude": "dark_orange",
    "gemini": "steel_blue1",
    "auditor": "dim",
}

ALERT_COLORS = {
    "green": "green",
    "yellow": "yellow",
    "red": "red",
}


def _drift_text(session: Session) -> Text:
    color = ALERT_COLORS[session.alert_level]
    return Text(f"● {session.drift_ratio}x", style=f"bold {color}")


def _role_text(session: Session) -> Text:
    color = PROVIDER_COLORS.get(session.entry.provider, "white")
    return Text(session.entry.role, style=f"bold {color}")


def _model_text(session: Session) -> Text:
    color = PROVIDER_COLORS.get(session.entry.provider, "white")
    label = "Claude" if session.entry.provider == "claude" else "Gemini"
    return Text(f"{label}/{session.entry.model}", style=color)


def print_report(sessions: list[Session]) -> None:
    if not sessions:
        console.print("[dim]No sessions found in agent-log.md[/dim]")
        return
    summary = get_summary(sessions)
    _print_summary_cards(summary)
    _print_sessions(sessions)
    _print_footer(summary)


def _print_summary_cards(summary: dict) -> None:
    total = summary["total_sessions"]
    claude_n = summary["claude_sessions"]
    gemini_n = summary["gemini_sessions"]
    red_n = summary["red_alerts"]

    def card(label: str, value: str, color: str) -> Panel:
        return Panel(
            f"[{color} bold]{value}[/{color} bold]\n[dim]{label}[/dim]",
            expand=True,
            border_style="dim",
        )

    console.print()
    console.print(
        Columns(
            [
                card("total sessions", str(total), "white"),
                card("Claude sessions", str(claude_n), "dark_orange"),
                card("Gemini sessions", str(gemini_n), "steel_blue1"),
                card("red alerts", str(red_n), "red" if red_n > 0 else "dim"),
            ]
        )
    )
    console.print()


def _print_sessions(sessions: list[Session]) -> None:
    table = Table(
        box=box.SIMPLE_HEAD,
        show_header=True,
        header_style="bold dim",
        show_edge=False,
        padding=(0, 1),
    )
    table.add_column("Date & Time", style="dim", width=20)
    table.add_column("Role", width=12)
    table.add_column("Model", width=14)
    table.add_column("Turns", justify="center", width=6)
    table.add_column("Drift", justify="right", width=8)

    for s in sessions:
        date_str = s.entry.date[:19] if len(s.entry.date) > 10 else s.entry.date[:10]
        table.add_row(
            date_str,
            _role_text(s),
            _model_text(s),
            str(s.turn_count),
            _drift_text(s),
        )

    console.print(table)
    console.print()


def _print_footer(summary: dict) -> None:
    worst = summary.get("worst")
    if not worst:
        return
    level_color = ALERT_COLORS[worst.alert_level]
    console.print(Rule(style="dim"))
    console.print(
        f"  Worst: [{level_color} bold]{worst.entry.role}·{worst.entry.model}"
        f"[/{level_color} bold]  "
        f"Drift: [{level_color} bold]{worst.drift_ratio}x[/{level_color} bold]  "
        f"Turns: [dim]{worst.turn_count}[/dim]"
    )
    if worst.alert_level == "red":
        console.print("  [red]→ Rotate this session now[/red]")
    console.print()


def print_worst(sessions: list[Session], limit: int = 5) -> None:
    sorted_sessions = sorted(sessions, key=lambda s: s.drift_ratio, reverse=True)
    console.print()
    console.print(f"[bold]Top {limit} sessions by drift[/bold]\n")
    _print_sessions(sorted_sessions[:limit])
