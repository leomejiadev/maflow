# multi-agent-workflow

A structured workflow to build software with multiple AI agents — without burning your token quota.

> By turn 100 of a Claude session, each turn costs 7x more than turn 1. By turn 300, it's 20x.
> This workflow keeps every session short, every agent focused, and every token intentional.

---

## Philosophy

**Claude is scarce — use it to think. Gemini is abundant — use it to build.**

Not every task needs the most powerful model. This workflow assigns the right agent to the right task, enforces strict context budgets, and eliminates token drift across sessions.

---

## Workflow at a glance

| Phase                                                          | Who                    | Tokens   |
|----------------------------------------------------------------|------------------------|----------|
| 0 · Setup — copy templates, fill SPEC.md sections 1–3          | You                    | 0        |
| 1 · Planning — Architect reads SPEC.md, writes ARCHITECTURE.md | Claude Sonnet / Opus   | Medium   |
| 1.5 · Plan review — read and approve the architecture          | You                    | 0        |
| 2 · Implementation — Worker builds layer by layer              | Gemini 2.5 Pro / Flash | Low      |
| 3 · Evaluation — Security, Tests, Quality run in parallel      | Gemini 2.5 Flash ×3    | Very low |
| 4 · Refactor — fix flagged issues, one file per session        | Claude Sonnet          | Medium   |
| 5 · Testing — Worker writes tests                              | Gemini 2.5 Flash       | Low      |
| 5.5 · Re-evaluation — Evaluators run again                     | Gemini 2.5 Flash ×3    | Very low |
| 6 · Final review — verify agent-log.md, close project          | You                    | 0        |

**The three phases where you intervene cost zero tokens and prevent hours of wasted work.**

### Agent model guide

| Role         | Model                                  | Use when                                   |
|--------------|----------------------------------------|--------------------------------------------|
| Architect    | Sonnet (default) · Opus (complex only) | New project · new module · breaking change |
| Worker       | Gemini 2.5 Pro                         | Services · LLM/RAG · complex logic         |
| Worker       | Gemini 2.5 Flash                       | CRUD · schemas · models · boilerplate      |
| Refactor     | Claude Sonnet                          | Dense logic · hidden coupling              |
| Evaluator ×3 | Gemini 2.5 Flash                       | End of every Worker or Refactor session    |

---

## Repository structure

```
multi-agent-workflow/
├── .cursorrules          # Auto-injected by Cursor — session rules, kept minimal
└── templates/
    ├── SPEC.md           # 👤 You fill sections 1–3 · 🤖 Architect fills 4–6
    ├── CLAUDE.md         # Agent roles, models, rules and close protocol
    ├── ARCHITECTURE.md   # Written by Architect · Worker implements against this
    ├── agent-log.md      # Session state · agents read last entry only
    └── decisions.md      # Architecture decisions · Architect writes · never re-discussed
```

Each file has one owner and one reader. No agent reads more than it needs.

---

## Getting started

**1. Copy templates into your project**
```bash
cp .cursorrules your-project/
cp templates/* your-project/
```

**2. Fill SPEC.md sections 1–3** — project name, scope, stack. No technical decisions yet. Takes 5 minutes.

**3. Run the Architect** — open Cursor, select Claude Sonnet, send:
```
Read SPEC.md. You are the Architect. Follow CLAUDE.md Role: Architect.
```
The Architect asks ≤3 questions, then produces `ARCHITECTURE.md` and `decisions.md`.

**4. Review the plan** — read `ARCHITECTURE.md`. Approve or adjust before any code is written. Zero tokens, maximum impact.

**5. Run the Worker** — switch to Gemini 2.5 Pro or Flash, send:
```
Read SPEC.md and ARCHITECTURE.md. You are the Worker.
Follow CLAUDE.md Role: Worker. Implement: [task from SPEC.md section 6]
```

**6. End every session with:**
```
Session complete. Run close protocol now.
```

**7. Run Evaluators** — three parallel Gemini 2.5 Flash sessions, one per sub-role:
```
You are the [Security / Test / Quality] Evaluator.
Follow CLAUDE.md Role: Evaluator. Evaluate: [paste file or diff]
```

**8. Repeat phases 4–5.5** — Refactor with Claude Sonnet, test with Gemini, evaluate again. Every session ends with the close protocol.

---

## Close protocol

Every agent ends every session with this exact format:

```
[DATE][ROLE·MODEL]
✅ DONE: [file · functions completed]
⏳ IN PROGRESS: [file · status — or N/A]
❌ PENDING: [file · not started — or N/A]
🚫 BLOCKED: [reason — or N/A]
➡️ NEXT: [ROLE·MODEL — exact task]
```

The `➡️ NEXT` field always specifies the next role and model:
```
➡️ NEXT: Worker·Pro — implement user_service.py
➡️ NEXT: Evaluator·Flash — evaluate user_service.py
➡️ NEXT: Refactor·Sonnet — reduce complexity in auth_service.py
```

The next agent reads only this entry — not the full codebase.

---

## Token efficiency

Four rules that compound across every project:

| Rule                                       | Effect                                   |
|--------------------------------------------|------------------------------------------|
| Each agent reads only its required files   | No wasted context at session start       |
| One task per session — stop if scope grows | Sessions stay short, cost stays flat     |
| Close protocol replaces codebase rereading | State is written once, not reconstructed |
| Cheap models handle cheap tasks            | Token budget matches task complexity     |

---

## Contributing

Open a PR with: what changed · why it saves tokens · which phase it affects.

## License
MIT
