"""
maflow orchestrator — automates workflow phases 2 through 5.5

Usage:
    python orchestrator.py --log agent-log.md --project .
    python orchestrator.py --log agent-log.md --project . --from-phase refactor
    python orchestrator.py --log agent-log.md --project . --dry-run
    python orchestrator.py --log agent-log.md --project . --timeout 900
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# Resolve auditor package — works whether maflow is installed globally or auditor/ is local
def _setup_auditor_path():
    try:
        import auditor

        return
    except ImportError:
        pass
    local = Path(__file__).parent / "auditor"
    if local.exists():
        sys.path.insert(0, str(Path(__file__).parent))
        return
    import importlib.util

    spec = importlib.util.find_spec("maflow")
    if spec and spec.submodule_search_locations:
        sys.path.insert(0, str(Path(spec.submodule_search_locations[0]).parent))
        return
    print(
        "ERROR: auditor package not found. Run: uv pip install -e /path/to/maflow --system"
    )
    sys.exit(1)


_setup_auditor_path()

from auditor.parser import parse_last_entry, parse_last_non_auditor_entry

DEFAULT_TIMEOUT = 600

PHASES = {
    "worker": {"next": "evaluator", "label": "Phase 2 — Worker"},
    "evaluator": {"next": "refactor", "label": "Phase 3 — Evaluators"},
    "refactor": {"next": "testing", "label": "Phase 4 — Refactor"},
    "testing": {"next": "reeval", "label": "Phase 5 — Testing"},
    "reeval": {"next": "done", "label": "Phase 5.5 — Re-evaluation"},
    "auditor": {"next": "worker", "label": "Resuming from audit"},
}

MODEL_CLAUDE = "Architect Refactor Sonnet"
MODEL_GEMINI = "Worker Evaluator Flash"

WORKER_PROMPT = """You are the Worker agent.
Read SPEC.md and ARCHITECTURE.md. Follow CLAUDE.md Role: Worker.
Implement the task in SPEC.md section 6 Next task field.
Run close protocol when done."""

EVALUATOR_SECURITY_PROMPT = """You are the Security Evaluator.
Follow CLAUDE.md Role: Evaluator — Security sub-role.
Read only: agent-log.md last entry (for target file) + that target file.
Write findings to agent-log.md. Run close protocol when done."""

EVALUATOR_TESTS_PROMPT = """You are the Test Evaluator.
Follow CLAUDE.md Role: Evaluator — Tests sub-role.
Read only: agent-log.md last entry (for target file) + that target file.
Write findings to agent-log.md. Run close protocol when done."""

EVALUATOR_QUALITY_PROMPT = """You are the Quality Evaluator.
Follow CLAUDE.md Role: Evaluator — Quality sub-role.
Read only: agent-log.md last entry (for target file) + that target file.
Write findings to agent-log.md. Run close protocol when done."""

REFACTOR_PROMPT = """You are the Refactor agent.
Read SPEC.md and the file flagged by evaluators in agent-log.md.
Follow CLAUDE.md Role: Refactor. One file only.
Run close protocol when done."""

TESTING_PROMPT = """You are the Worker agent writing tests.
Read SPEC.md and the last refactored file in agent-log.md.
Follow CLAUDE.md Role: Worker. Write tests for that file.
Run close protocol when done."""

REEVAL_SECURITY_PROMPT = """You are the Security Evaluator running re-evaluation.
Follow CLAUDE.md Role: Evaluator — Security sub-role.
Read only: agent-log.md last entry (for target file) + that target file.
Write findings to agent-log.md. Run close protocol when done."""

REEVAL_TESTS_PROMPT = """You are the Test Evaluator running re-evaluation.
Follow CLAUDE.md Role: Evaluator — Tests sub-role.
Read only: agent-log.md last entry (for target file) + that target file.
Write findings to agent-log.md. Run close protocol when done."""

REEVAL_QUALITY_PROMPT = """You are the Quality Evaluator running re-evaluation.
Follow CLAUDE.md Role: Evaluator — Quality sub-role.
Read only: agent-log.md last entry (for target file) + that target file.
Write findings to agent-log.md. Run close protocol when done."""


def _log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


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


_CN = _find_cn()


def _check_spec_ready(project: str) -> bool:
    spec_path = Path(project) / "SPEC.md"
    if not spec_path.exists():
        _log("SPEC.md not found — create it before running the orchestrator")
        return False
    content = spec_path.read_text(encoding="utf-8", errors="replace")
    if "[Architect defines]" in content:
        _log("SPEC.md section 4 not filled — run the Architect first (Phase 1)")
        return False
    return True


def _run_cn(
    prompt: str,
    project: str,
    model: str = "",
    timeout: int = DEFAULT_TIMEOUT,
    dry_run: bool = False,
) -> bool:
    cmd = [_CN, "-p", prompt, "--allow", "Write"]
    if model:
        cmd += ["--model", model]
    if dry_run:
        _log(
            f"[DRY RUN] Would run: cn -p '{prompt[:60]}...' model={model or 'default'}"
        )
        return True
    _log(f"Running agent: {prompt[:60]}... [{model or 'default'}]")
    try:
        env = {**os.environ, "PYTHONUTF8": "1"}
        result = subprocess.run(
            cmd,
            cwd=project,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        if result.returncode != 0:
            _log(f"Agent failed: {result.stderr[:200]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        _log(f"Agent timed out after {timeout}s — increase with --timeout")
        return False
    except FileNotFoundError:
        _log("cn not found — install with: npm i -g @continuedev/cli")
        return False


def _run_parallel(
    prompts: list[str],
    project: str,
    model: str = "",
    timeout: int = DEFAULT_TIMEOUT,
    dry_run: bool = False,
) -> bool:
    if dry_run:
        for p in prompts:
            _log(
                f"[DRY RUN] Would run parallel: cn -p '{p[:50]}...' model={model or 'default'}"
            )
        return True
    env = {**os.environ, "PYTHONUTF8": "1"}
    processes = []
    for prompt in prompts:
        cmd = [_CN, "-p", prompt, "--allow", "Write"]
        if model:
            cmd += ["--model", model]
        proc = subprocess.Popen(
            cmd,
            cwd=project,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        processes.append(proc)
        _log(f"Spawned evaluator: {prompt[:50]}...")
    results = []
    for proc in processes:
        try:
            proc.communicate(timeout=timeout)
            results.append(proc.returncode == 0)
        except subprocess.TimeoutExpired:
            proc.kill()
            results.append(False)
    return all(results)


def _check_blocked(log_path: Path) -> bool:
    entry = parse_last_non_auditor_entry(log_path)
    if not entry:
        return False
    blocked = entry.blocked.strip().upper()
    return blocked not in ("N/A", "", "NA")


def _run_audit(log_path: Path) -> None:
    try:
        subprocess.run(
            ["maflow", "report", "--log", str(log_path)], capture_output=True
        )
    except FileNotFoundError:
        pass


def _detect_current_phase(log_path: Path) -> str:
    entry = parse_last_entry(log_path)
    if not entry:
        return "worker"
    role = entry.role.lower()
    if role in PHASES:
        return PHASES[role]["next"]
    return "worker"


def run_pipeline(
    log_path: Path,
    project: str,
    from_phase: str = "",
    timeout: int = DEFAULT_TIMEOUT,
    dry_run: bool = False,
) -> None:
    if not log_path.exists():
        _log(f"agent-log.md not found at {log_path}")
        return

    current = from_phase if from_phase else _detect_current_phase(log_path)

    if current == "worker" and not dry_run:
        if not _check_spec_ready(project):
            return

    _log(f"Starting pipeline from phase: {current}")

    while current != "done":
        _log(f"─── {PHASES.get(current, {}).get('label', current)} ───")

        if current == "worker":
            ok = _run_cn(WORKER_PROMPT, project, MODEL_GEMINI, timeout, dry_run)
        elif current == "evaluator":
            ok = _run_parallel(
                [
                    EVALUATOR_SECURITY_PROMPT,
                    EVALUATOR_TESTS_PROMPT,
                    EVALUATOR_QUALITY_PROMPT,
                ],
                project,
                MODEL_GEMINI,
                timeout,
                dry_run,
            )
        elif current == "refactor":
            ok = _run_cn(REFACTOR_PROMPT, project, MODEL_CLAUDE, timeout, dry_run)
        elif current == "testing":
            ok = _run_cn(TESTING_PROMPT, project, MODEL_GEMINI, timeout, dry_run)
        elif current == "reeval":
            ok = _run_parallel(
                [REEVAL_SECURITY_PROMPT, REEVAL_TESTS_PROMPT, REEVAL_QUALITY_PROMPT],
                project,
                MODEL_GEMINI,
                timeout,
                dry_run,
            )
        else:
            _log(f"Unknown phase: {current}")
            break

        if not ok:
            _log(f"Phase {current} failed — stopping pipeline")
            break

        _run_audit(log_path)

        if _check_blocked(log_path):
            entry = parse_last_non_auditor_entry(log_path)
            _log(f"BLOCKED detected: {entry.blocked}")
            _log("Pipeline paused — resolve the block and re-run")
            break

        current = PHASES.get(current, {}).get("next", "done")
        if current != "done":
            time.sleep(2)

    if current == "done":
        _log("Pipeline complete — ready for Phase 6 review")
        _run_audit(log_path)


def main():
    parser = argparse.ArgumentParser(description="maflow orchestrator")
    parser.add_argument("--log", default="agent-log.md")
    parser.add_argument("--project", default=".")
    parser.add_argument("--from-phase", default="")
    parser.add_argument("--timeout", default=DEFAULT_TIMEOUT, type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_pipeline(
        Path(args.log), args.project, args.from_phase, args.timeout, args.dry_run
    )


if __name__ == "__main__":
    main()
