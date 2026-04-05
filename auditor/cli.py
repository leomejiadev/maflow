from pathlib import Path

import typer

from .alerts import print_alert
from .parser import parse_log
from .report import console, print_report, print_worst
from .tracker import get_summary, process_entries
from .writer import write_audit_entry

app = typer.Typer(
    name="maflow audit",
    help="Token usage auditor for multi-agent-workflow.",
    add_completion=False,
)

DEFAULT_LOG = Path("agent-log.md")


def _load(log_path: Path):
    if not log_path.exists():
        console.print(f"[red]agent-log.md not found at: {log_path}[/red]")
        raise typer.Exit(1)
    entries = parse_log(log_path)
    if not entries:
        console.print("[dim]No entries found in agent-log.md[/dim]")
        raise typer.Exit(0)
    return process_entries(entries)


@app.command()
def report(
    log: Path = typer.Option(DEFAULT_LOG, "--log", "-l", help="Path to agent-log.md"),
    write: bool = typer.Option(
        False, "--write", help="Write audit entry to log after report"
    ),
):
    """Full audit report with drift ratio per session."""
    sessions = _load(log)
    print_report(sessions)
    if write:
        write_audit_entry(log, sessions)
        console.print(f"[dim]Audit entry written to {log}[/dim]")


@app.command()
def sessions(
    log: Path = typer.Option(DEFAULT_LOG, "--log", "-l", help="Path to agent-log.md"),
):
    """List all sessions with alert status."""
    sessions = _load(log)
    for s in sessions:
        print_alert(s)
    summary = get_summary(sessions)
    console.print(
        f"\n[dim]Total: {summary['total_sessions']} · "
        f"Claude: {summary['claude_sessions']} · "
        f"Gemini: {summary['gemini_sessions']}[/dim]"
    )


@app.command()
def worst(
    log: Path = typer.Option(DEFAULT_LOG, "--log", "-l", help="Path to agent-log.md"),
    limit: int = typer.Option(
        5, "--limit", "-n", help="Number of worst sessions to show"
    ),
):
    """Show worst sessions by drift ratio."""
    sessions_list = _load(log)
    print_worst(sessions_list, limit=limit)


if __name__ == "__main__":
    app()
