import os
import shutil
import subprocess
from pathlib import Path

import typer

from .alerts import print_alert
from .parser import parse_last_entry, parse_log
from .report import console, print_report, print_worst
from .tracker import get_summary, process_entries
from .writer import write_audit_entry

app = typer.Typer(
    name="maflow",
    help="Multi-agent workflow CLI — audit, report and run agents.",
    add_completion=False,
)

DEFAULT_LOG = (
    Path("workflow/agent-log.md")
    if Path("workflow/agent-log.md").exists()
    else Path("agent-log.md")
)

MODEL_CLAUDE = "Architect Refactor Sonnet"
MODEL_GEMINI = "Worker Evaluator Flash"

PROMPTS = {
    "architect": """You are the Architect agent.
Read SPEC.md sections 1-3. Follow CLAUDE.md Role: Architect.
Define architecture, write ARCHITECTURE.md and decisions.md.
Run close protocol when done.""",
    "worker": """You are the Worker agent.
Read SPEC.md and ARCHITECTURE.md. Follow CLAUDE.md Role: Worker.
Implement the task in SPEC.md section 6 Next task field.
If you use a new external package: add it to pyproject.toml with exact version before importing it.
Run close protocol when done.""",
    "evaluator-security": """You are the Security Evaluator.
Follow CLAUDE.md Role: Evaluator — Security sub-role.
Read only agent-log.md last entry and the target file.
Write findings to agent-log.md. Run close protocol when done.""",
    "evaluator-tests": """You are the Test Evaluator.
Follow CLAUDE.md Role: Evaluator — Tests sub-role.
Read only agent-log.md last entry and the target file.
Write findings to agent-log.md. Run close protocol when done.""",
    "evaluator-quality": """You are the Quality Evaluator.
Follow CLAUDE.md Role: Evaluator — Quality sub-role.
Read only agent-log.md last entry and the target file.
Write findings to agent-log.md. Run close protocol when done.""",
    "refactor": """You are the Refactor agent.
Read SPEC.md and the file flagged by evaluators in agent-log.md.
Follow CLAUDE.md Role: Refactor. One file only.
If you use a new external package: add it to pyproject.toml with exact version before importing it.
Run close protocol when done.""",
    "testing": """You are the Worker agent writing tests.
Read SPEC.md and the last refactored file in agent-log.md.
Follow CLAUDE.md Role: Worker. Write tests for that file.
Run close protocol when done.""",
}


def _find_cn() -> str:
    found = shutil.which("cn")
    if found:
        return found
    candidates = [
        os.path.expanduser(r"~\AppData\Roaming\npm\cn.cmd"),
        os.path.expanduser(r"~\AppData\Roaming\npm\cn"),
        os.path.expanduser("~/.npm-global/bin/cn"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "cn"


def _check_docker(project: Path) -> bool:
    """Check Docker is running and PostgreSQL container is up. Ask permission if not."""
    result = subprocess.run(["docker", "info"], capture_output=True, text=True)
    docker_down = (
        result.returncode != 0
        or "failed to connect" in result.stderr.lower()
        or "cannot connect" in result.stderr.lower()
        or "error" in result.stderr.lower()
    )

    if docker_down:
        console.print("[yellow]⚠  Docker is not running.[/yellow]")
        start = typer.confirm("   Start Docker Desktop now?", default=False)
        if not start:
            console.print("[dim]   Skipping Docker — continue manually.[/dim]")
            return True
        console.print("[dim]   Start Docker Desktop manually then press Enter...[/dim]")
        input()
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        still_down = (
            result.returncode != 0
            or "failed to connect" in result.stderr.lower()
            or "error" in result.stderr.lower()
        )
        if still_down:
            console.print(
                "[red]   Docker still not running — continuing without it.[/red]"
            )
            return True

    # Check docker-compose.yml
    compose_file = project / "docker-compose.yml"
    if not compose_file.exists():
        console.print("[yellow]⚠  No docker-compose.yml found.[/yellow]")
        create = typer.confirm(
            "   Create a default PostgreSQL docker-compose.yml?", default=True
        )
        if create:
            compose_file.write_text(
                "services:\n"
                "  db:\n"
                "    image: postgres:16\n"
                "    environment:\n"
                "      POSTGRES_USER: postgres\n"
                "      POSTGRES_PASSWORD: postgres\n"
                "      POSTGRES_DB: app_db\n"
                "    ports:\n"
                '      - "5432:5432"\n',
                encoding="utf-8",
            )
            console.print("[green]   ✓ docker-compose.yml created[/green]")
        else:
            return True

    # Check if container is running
    result = subprocess.run(
        ["docker", "compose", "ps", "--status", "running"],
        capture_output=True,
        text=True,
        cwd=str(project),
    )
    container_up = "postgres" in result.stdout.lower() or "db" in result.stdout.lower()
    if not container_up:
        console.print("[yellow]⚠  PostgreSQL container is not running.[/yellow]")
        start = typer.confirm("   Run docker compose up -d?", default=True)
        if start:
            result = subprocess.run(
                ["docker", "compose", "up", "-d"], cwd=str(project), text=True
            )
            if result.returncode == 0:
                console.print("[green]   ✓ PostgreSQL container started[/green]")
            else:
                console.print(
                    "[red]   Failed to start — check docker-compose.yml[/red]"
                )
        else:
            console.print(
                "[dim]   Skipping — ensure DB is running before migrations.[/dim]"
            )

    return True


def _print_error(line: str) -> None:
    """Parse cn error JSON and show a clean human-readable message."""
    import json
    import re

    try:
        # cn wraps errors in nested JSON strings — extract the innermost message
        outer = json.loads(line)
        raw = outer.get("message", "")
        # Unescape nested JSON
        raw = raw.replace('"', '"').replace("\n", " ")
        # Extract rate limit info
        if "429" in raw or "quota" in raw.lower() or "rate" in raw.lower():
            retry = re.search(r"retry[^\d]*(\d+)", raw, re.IGNORECASE)
            retry_str = f" — retry in {retry.group(1)}s" if retry else ""
            console.print(f"[yellow]⚠  Gemini rate limit reached{retry_str}[/yellow]")
            console.print(
                "[dim]   Free tier: 20 requests/day. Resets at midnight Pacific time.[/dim]"
            )
        elif "401" in raw or "auth" in raw.lower() or "api key" in raw.lower():
            console.print(
                "[red]✗  API key error — check your Gemini key in ~/.continue/config.yaml[/red]"
            )
        elif "timeout" in raw.lower():
            console.print("[red]✗  Request timed out — try again[/red]")
        else:
            # Show first 120 chars of cleaned message
            clean = re.sub(r'[{}"\\/]', "", raw)[:120]
            console.print(f"[red]✗  Error: {clean}[/red]")
    except Exception:
        # Fallback — show truncated raw
        console.print(f"[red]✗  {line[:120]}[/red]")


def _run_agent(role: str, model: str, log: Path) -> None:
    """Launch cn with live spinner so you can watch the agent work."""
    cn = _find_cn()
    prompt = PROMPTS[role]

    console.print(f"\n[bold]● {role}[/bold] [{model}]")
    console.rule(style="dim")

    env = {**os.environ, "PYTHONUTF8": "1", "FORCE_COLOR": "1"}

    try:
        import threading
        import time

        from rich.live import Live
        from rich.text import Text as RichText

        output_lines = []
        proc = subprocess.Popen(
            [cn, "-p", prompt, "--model", model, "--allow", "Write"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        def _read():
            for line in proc.stdout:
                output_lines.append(line.rstrip())

        reader = threading.Thread(target=_read, daemon=True)
        reader.start()

        with Live(console=console, refresh_per_second=4) as live:
            while proc.poll() is None:
                last = output_lines[-1] if output_lines else ""
                status = (
                    last[:70]
                    if last and not last.startswith("{")
                    else (
                        output_lines[-2][:70]
                        if len(output_lines) > 1
                        and not output_lines[-2].startswith("{")
                        else "working..."
                    )
                )
                live.update(RichText(f"  ⟳  {status}", style="dim"))
                time.sleep(0.25)

        reader.join()
        proc.wait()

        for line in output_lines:
            if not line:
                continue
            if line.startswith("{") and "error" in line.lower():
                _print_error(line)
            elif any(k in line for k in ["✅", "DONE", "NEXT", "BLOCKED"]):
                console.print(f"[dim green]  {line}[/dim green]")
            else:
                console.print(f"[dim]  {line}[/dim]")

    except FileNotFoundError:
        console.print(
            "[red]cn not found — install with: npm i -g @continuedev/cli[/red]"
        )
        return

    console.rule(style="dim")
    console.print("[dim]Session ended. Running audit...[/dim]\n")
    if log.exists():
        entries = parse_log(log)
        if entries:
            sessions = process_entries(entries)
            print_report(sessions)


def _load(log_path: Path):
    if not log_path.exists():
        console.print(f"[red]agent-log.md not found at: {log_path}[/red]")
        raise typer.Exit(1)
    entries = parse_log(log_path)
    if not entries:
        console.print("[dim]No entries found in agent-log.md[/dim]")
        raise typer.Exit(0)
    return process_entries(entries)


def _get_templates_dir() -> Path:
    import auditor

    candidates = [
        Path(auditor.__file__).parent.parent / "templates",
        Path(auditor.__file__).parent / "templates",
        Path(__file__).parent.parent / "templates",
        Path.home() / "Desktop" / "maflow" / "templates",
    ]
    for p in candidates:
        if p.exists() and any(p.iterdir()):
            return p
    raise FileNotFoundError(
        "templates/ not found.\n"
        "Install from the correct directory:\n"
        "  cd ~/Desktop/maflow && uv pip install -e . --system"
    )


# ── Init ───────────────────────────────────────────────────────────────────


@app.command()
def init(
    project_name: str = typer.Argument(..., help="Name of the new project"),
    path: Path = typer.Option(
        Path("."), "--path", "-p", help="Where to create the project"
    ),
):
    """Scaffold a new project with the maflow workflow structure."""
    project_dir = path / project_name
    if project_dir.exists():
        console.print(f"[red]Directory already exists: {project_dir}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Creating project:[/bold] {project_name}")

    workflow_dir = project_dir / "workflow"
    continue_dir = project_dir / ".continue"
    workflow_dir.mkdir(parents=True)
    continue_dir.mkdir(parents=True)

    try:
        templates_dir = _get_templates_dir()
        for f in templates_dir.iterdir():
            if f.is_file():
                shutil.copy(f, workflow_dir / f.name)
        console.print(
            "  [green]✓[/green] workflow/ — SPEC.md · CLAUDE.md · ARCHITECTURE.md · agent-log.md · decisions.md"
        )
    except FileNotFoundError:
        console.print(
            "  [yellow]⚠[/yellow] templates not found — create workflow/ files manually"
        )

    (continue_dir / "config.yaml").write_text(
        "name: maflow\nversion: 1.0.0\nschema: v1\n", encoding="utf-8"
    )
    console.print("  [green]✓[/green] .continue/config.yaml")

    import auditor as _pkg

    orch = Path(_pkg.__file__).parent.parent / "orchestrator.py"
    if orch.exists():
        shutil.copy(orch, project_dir / "orchestrator.py")
        console.print("  [green]✓[/green] orchestrator.py")

    (project_dir / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n*.db\n.env\n*.egg-info/\ndist/\n.DS_Store\n.venv/\n",
        encoding="utf-8",
    )
    console.print("  [green]✓[/green] .gitignore")

    result = subprocess.run(
        ["uv", "venv", str(project_dir / ".venv")], capture_output=True, text=True
    )
    if result.returncode == 0:
        console.print("  [green]✓[/green] .venv/")
    else:
        console.print("  [yellow]⚠[/yellow] .venv not created — run 'uv venv' manually")

    console.print(f"\n[bold green]Project ready:[/bold green] {project_dir}")
    console.print("\n[dim]Next steps:[/dim]")
    console.print(f"  cd {project_name}")
    console.print("  Fill workflow/SPEC.md sections 1-3")
    console.print("  maflow architect")


# ── Agent commands ─────────────────────────────────────────────────────────


@app.command()
def architect(
    log: Path = typer.Option(DEFAULT_LOG, "--log", "-l"),
):
    """Phase 1 — Run the Architect agent (Claude Sonnet)."""
    _run_agent("architect", MODEL_CLAUDE, log)


@app.command()
def worker(
    log: Path = typer.Option(DEFAULT_LOG, "--log", "-l"),
    skip_docker: bool = typer.Option(False, "--skip-docker", help="Skip Docker check"),
):
    """Phase 2 — Run the Worker agent (Gemini Flash)."""
    if not skip_docker:
        _check_docker(Path("."))
    _run_agent("worker", MODEL_GEMINI, log)


@app.command()
def evaluator(
    log: Path = typer.Option(DEFAULT_LOG, "--log", "-l"),
):
    """Phase 3 — Run all 3 Evaluators sequentially (Gemini Flash)."""
    console.print("\n[bold]Running 3 evaluators sequentially[/bold]")
    for role in ["evaluator-security", "evaluator-tests", "evaluator-quality"]:
        console.print(f"\n[dim]── {role} ──[/dim]")
        _run_agent(role, MODEL_GEMINI, log)


@app.command()
def refactor(
    log: Path = typer.Option(DEFAULT_LOG, "--log", "-l"),
    skip_docker: bool = typer.Option(False, "--skip-docker", help="Skip Docker check"),
):
    """Phase 4 — Run the Refactor agent (Claude Sonnet)."""
    if not skip_docker:
        _check_docker(Path("."))
    _run_agent("refactor", MODEL_CLAUDE, log)


@app.command()
def testing(
    log: Path = typer.Option(DEFAULT_LOG, "--log", "-l"),
    skip_docker: bool = typer.Option(False, "--skip-docker", help="Skip Docker check"),
):
    """Phase 5 — Run the Testing agent (Gemini Flash)."""
    if not skip_docker:
        _check_docker(Path("."))
    _run_agent("testing", MODEL_GEMINI, log)


@app.command()
def status(
    log: Path = typer.Option(DEFAULT_LOG, "--log", "-l"),
):
    """Show current project status from agent-log.md."""
    entry = parse_last_entry(log)
    if not entry:
        console.print("[dim]No entries in agent-log.md yet[/dim]")
        return
    console.print(f"\n[bold]Last session:[/bold] {entry.role} · {entry.model}")
    console.print(f"[green]Done:[/green] {entry.done}")
    console.print(f"[yellow]Next:[/yellow] {entry.next_task}")
    if entry.blocked and entry.blocked.upper() not in ("N/A", ""):
        console.print(f"[red]Blocked:[/red] {entry.blocked}")


# ── Audit commands ─────────────────────────────────────────────────────────


@app.command()
def report(
    log: Path = typer.Option(DEFAULT_LOG, "--log", "-l"),
    write: bool = typer.Option(False, "--write"),
):
    """Audit report with drift ratio per session."""
    sessions = _load(log)
    print_report(sessions)
    if write:
        write_audit_entry(log, sessions)
        console.print(f"[dim]Audit entry written to {log}[/dim]")


@app.command()
def sessions(
    log: Path = typer.Option(DEFAULT_LOG, "--log", "-l"),
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
    log: Path = typer.Option(DEFAULT_LOG, "--log", "-l"),
    limit: int = typer.Option(5, "--limit", "-n"),
):
    """Show worst sessions by drift ratio."""
    sessions_list = _load(log)
    print_worst(sessions_list, limit=limit)


@app.command()
def fix_log(
    log: Path = typer.Option(DEFAULT_LOG, "--log", "-l"),
):
    """Fix encoding issues in agent-log.md."""
    if not log.exists():
        console.print(f"[red]Not found: {log}[/red]")
        raise typer.Exit(1)

    content = log.read_text(encoding="utf-8", errors="replace")
    replacements = {
        "\ufffd": "·",
        "M-BM-7": "·",
        "â€¢": "·",
        "?? DONE:": "✅ DONE:",
        "? DONE:": "✅ DONE:",
        "? IN PROGRESS:": "⏳ IN PROGRESS:",
        "?? IN PROGRESS:": "⏳ IN PROGRESS:",
        "? PENDING:": "❌ PENDING:",
        "?? PENDING:": "❌ PENDING:",
        "?? BLOCKED:": "🚫 BLOCKED:",
        "? BLOCKED:": "🚫 BLOCKED:",
        "?? NEXT:": "➡️ NEXT:",
        "? NEXT:": "➡️ NEXT:",
    }
    fixed = content
    for bad, good in replacements.items():
        fixed = fixed.replace(bad, good)
    log.write_text(fixed, encoding="utf-8")
    console.print(f"[green]Fixed encoding in {log}[/green]")


if __name__ == "__main__":
    app()
