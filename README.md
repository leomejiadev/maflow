# maflow

Token-efficient multi-agent workflow for Python backend development.

**Philosophy:** Claude thinks, Gemini builds. Each agent does one thing per session and closes with a structured log entry. The auditor measures drift so you know when to rotate.

---

## How it works

```
You → fill SPEC.md (5 min)
Architect (Claude Sonnet) → ARCHITECTURE.md + pyproject.toml
You → review the plan
Worker (Gemini Flash) → implements one file per session
Evaluator x3 (Gemini Flash) → security · tests · quality
Refactor (Claude Sonnet) → fixes flagged issues
Testing (Gemini Flash) → writes tests
You → review agent-log.md
```

---

## Install

```bash
git clone https://github.com/leomejiadev/maflow.git
cd maflow
uv pip install -e . --system
npm i -g @continuedev/cli
```

---

## New project

```bash
maflow init my-project
cd my-project
# Fill workflow/SPEC.md sections 1-3
maflow architect
```

---

## Workflow commands

```bash
maflow architect    # Phase 1 — plan + pyproject.toml
maflow worker       # Phase 2 — implement
maflow evaluator    # Phase 3 — evaluate x3
maflow refactor     # Phase 4 — fix issues
maflow testing      # Phase 5 — write tests
```

## Audit commands

```bash
maflow status       # current project state
maflow report       # drift report per session
maflow worst        # sessions with highest drift
maflow fix-log      # repair encoding issues on Windows
```

---

## Project structure

```
my-project/
├── .continue/config.yaml   # Continue.dev workspace config
├── workflow/
│   ├── SPEC.md             # you fill 1-3 · Architect fills 4-7
│   ├── CLAUDE.md           # agent roles and rules
│   ├── ARCHITECTURE.md     # Architect writes this
│   ├── agent-log.md        # session history and audit trail
│   └── decisions.md        # architecture decision records
├── orchestrator.py         # automated pipeline (Mac/Linux)
└── app/                    # your code lives here
```

---

## Models

| Role | Model | When |
|---|---|---|
| Architect | Claude Sonnet | new project · new module |
| Worker | Gemini Flash | any implementation task |
| Evaluator | Gemini Flash | after every Worker session |
| Refactor | Claude Sonnet | dense logic · coupling detected |
| Testing | Gemini Flash | after refactor |

---

## Notes

- Orchestrator (`python orchestrator.py`) requires Mac or Linux — cn CLI has a known bug on Windows
- Free Gemini tier: 20 requests/day, resets at midnight Pacific time
- Drift alert levels: ● green <2x · ● yellow 2-4x · ● red >4x → rotate session