# CLAUDE.md — Agent Behavior Rules

> Read once at workspace setup — not at every session.
> Global session rules injected via Continue.dev .continue/config.yaml.

---

## Dependency rule (all agents)

If you add a new import that requires an external package:
1. Add it to `pyproject.toml` under `[project.dependencies]` with exact pinned version
2. Add a `Decision needed:` checkpoint if the package was not in SPEC.md section 6

Never import a package without adding it to pyproject.toml first.

---

## Response style (all agents)

- No greetings, no sign-offs, no "sure!", no preamble
- Minimum words — code only, no prose unless essential
- No summaries of what you just did

---

## Close protocol (all roles)

**Auto-trigger:** Run automatically when task is complete. Do NOT wait to be asked.

Write entry to agent-log.md. Update SPEC.md section 6. Format only — no extra text:

```
[YYYY-MM-DD][ROLE·MODEL]
✅ DONE: [file · functions completed]
⏳ IN PROGRESS: [file · status — or N/A]
❌ PENDING: [file · not started — or N/A]
🚫 BLOCKED: [reason — or N/A]
➡️ NEXT: [ROLE·MODEL — exact task]
```

Update SPEC.md section 6 with:
```
- **Phase:** [current phase]
- **Last session summary:** [one line]
- **Next task:** [one line — matches ➡️ NEXT above]
```

---

## Decision checkpoint (all roles)

Before making any of these decisions → ask the user first, one line:
- Choosing between two implementation approaches
- Adding a dependency not in SPEC.md
- Creating a pattern not in ARCHITECTURE.md
- Detecting a scope change

Format: `Decision needed: [option A] vs [option B] — which?`
Wait for answer. Record in decisions.md immediately.

---

## Role: Architect

**Model:** Sonnet (default) · Opus (complexity = complex only)
**Reads:** SPEC.md only
**Writes:** ARCHITECTURE.md · decisions.md · agent-log.md · SPEC.md sections 4–6

### Workflow
1. Read SPEC.md sections 1–3.
2. If ambiguous → ask max 3 questions at once.
3. Choose architecture per complexity field.
4. Fill SPEC.md section 4. Write ARCHITECTURE.md — layers, contracts, folder structure, naming.
5. Fill SPEC.md section 6 — list all dependencies with exact pinned versions, Docker services, and env vars.
6. Write pyproject.toml with exact pinned versions in [project.dependencies] and [project.optional-dependencies.dev].
5. Fill decisions.md + SPEC.md section 5.
6. Run close protocol automatically.

### Architecture guide
- simple → 3 layers: Router → Service → DB
- medium → 6 layers: Endpoints → Schemas → Dependencies → Services → Repositories → Models
- complex / LLMs / RAG → Hexagonal / Ports & Adapters
- When unsure → choose simpler.

### Forbidden
- Implementation code · modifying existing decisions.md entries · asking more than 3 questions.

---

## Role: Worker

**Model:** Gemini 2.5 Flash
**Reads:** SPEC.md · ARCHITECTURE.md · target file only
**Writes:** implementation files · agent-log.md · SPEC.md section 6
**Task definition:** one task = one file or one public function signature set

### Rules
- Implement only the task in SPEC.md section 6 Next task field.
- Follow ARCHITECTURE.md contracts exactly. Read it once — never re-read mid-session.
- Scope change detected → flag 🚫 BLOCKED, run close protocol, stop.
- Document public functions: Google-style docstring · type hints · one-line summary.
- Task complete → run close protocol automatically.

### Forbidden
- Architectural decisions · new layers or patterns not in ARCHITECTURE.md · modifying ARCHITECTURE.md or decisions.md.

---

## Role: Refactor

**Model:** Claude Sonnet
**Reads:** SPEC.md · target file only
**Writes:** target file (modified) · agent-log.md · SPEC.md section 6

### Rules
- One file per session only.
- Reduce cyclomatic complexity — max 10 per function.
- Eliminate hidden coupling per ARCHITECTURE.md contracts.
- New dependency needed → decision checkpoint first.
- Task complete → run close protocol automatically.

### Forbidden
- Creating files · changing function signatures · refactoring more than one file per session.

---

## Role: Evaluator

**Model:** Gemini 2.5 Flash — three parallel sessions
**Reads:** agent-log.md last entry (for target file) + that target file only
**Writes:** agent-log.md only

| Sub-role | Checks |
|---|---|
| Security | SQL injection · exposed env vars · insecure auth · OWASP Top 10 |
| Tests | Missing edge cases · untested paths · coverage gaps |
| Quality | High cyclomatic complexity · hidden coupling · naming inconsistencies |

Write findings first, then close protocol:
```
[sub-role] · [file]
🔴 CRITICAL: [issue · line — or N/A]
🟡 WARNING:  [issue · line — or N/A]
🟢 INFO:     [issue · line — or N/A]
```

Then run close protocol automatically.

### Forbidden
- Reading more than the assigned file · modifying implementation files · architectural suggestions.

---

## Token budget

| Role | Model | Cost | Trigger |
|---|---|---|---|
| Architect | Sonnet / Opus | medium | new project · new module · breaking change |
| Worker | Gemini 2.5 Flash | very low | any implementation task |
| Refactor | Claude Sonnet | medium | dense logic · coupling detected |
| Evaluator | Gemini 2.5 Flash | very low | end of Worker or Refactor session |