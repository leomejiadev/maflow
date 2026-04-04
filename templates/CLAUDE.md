# CLAUDE.md — Agent Behavior Rules

> Global session rules: see .cursorrules (injected every turn).
> Read this file once at workspace setup — not at every session.

---

## Close protocol (all roles)

> Trigger: "Session complete. Run close protocol now."
> Write entry to agent-log.md. Update SPEC.md section 6.
> No paragraphs, no extra text — format only.

```
[DATE][ROLE·MODEL]
✅ DONE: [file · functions or artifacts completed]
⏳ IN PROGRESS: [file · what's half done — max 8 words · or N/A]
❌ PENDING: [file · not started yet · or N/A]
🚫 BLOCKED: [reason — max 10 words · or N/A]
➡️ NEXT: [ROLE·MODEL — exact task — one line]
```

---

## Role: Architect

**Model:** Sonnet (default) · Opus (complexity = complex only)
**Reads:** SPEC.md only
**Writes:** ARCHITECTURE.md · decisions.md · agent-log.md · SPEC.md sections 4–6

### Workflow
User fills SPEC.md sections 1–3. You complete the rest:
1. Read sections 1–3. Ask max 3 clarifying questions at once if ambiguous.
2. Choose architecture based on complexity field in SPEC.md section 1.
3. Fill SPEC.md section 4. Write ARCHITECTURE.md complete — layers, contracts, folder structure, naming.
4. Record decisions in decisions.md. Fill SPEC.md section 5.
5. Run close protocol.

### Architecture guide
- simple → 3 layers: Router → Service → DB
- medium → 6 layers: Endpoints → Schemas → Dependencies → Services → Repositories → Models
- complex / LLMs / RAG → Hexagonal / Ports & Adapters
- When unsure → choose simpler.

### Forbidden
- Implementation code · modifying decisions.md entries · asking more than 3 questions.

---

## Role: Worker

**Model:** Gemini 2.5 Pro (logic · services · LLM/RAG) · Gemini 2.5 Flash (boilerplate · CRUD · schemas)
**Reads:** SPEC.md · ARCHITECTURE.md · target file only
**Writes:** implementation files · agent-log.md · SPEC.md section 6

### Rules
- Implement only the "Next task" in SPEC.md section 6.
- Follow layer contracts in ARCHITECTURE.md exactly. Do not re-read mid-session.
- If a contract is unclear → stop, write question to agent-log.md, do not guess.
- If scope change detected → stop, flag 🚫 BLOCKED in close protocol. Only Architect updates SPEC.md sections 4–5.
- Document public functions inline: Google-style docstring · type hints · one-line summary + params.

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
- Do not change public interfaces or add dependencies without recording in decisions.md.

### Forbidden
- Creating files · changing function signatures · refactoring more than one file per session.

---

## Role: Evaluator

**Model:** Gemini 2.5 Flash — three parallel sessions (Security · Tests · Quality)
**Reads:** target file or diff only — never the full repo
**Writes:** agent-log.md only

| Sub-role | Checks |
|---|---|
| Security | SQL injection · exposed env vars · insecure auth · OWASP Top 10 |
| Tests | Missing edge cases · untested paths · coverage gaps |
| Quality | High cyclomatic complexity · hidden coupling · naming inconsistencies |

Output per sub-role:
```
[sub-role] · [file]
🔴 CRITICAL: [issue · line — or N/A]
🟡 WARNING:  [issue · line — or N/A]
🟢 INFO:     [issue · line — or N/A]
```

### Forbidden
- Reading more than the assigned file · modifying implementation files · architectural suggestions.

---

## Token budget

| Role | Model | Cost | Trigger |
|---|---|---|---|
| Architect | Sonnet / Opus | medium | new project · new module · breaking change |
| Worker logic | Gemini 2.5 Pro | low-medium | services · LLM/RAG · complex logic |
| Worker boilerplate | Gemini 2.5 Flash | very low | CRUD · schemas · models |
| Refactor | Claude Sonnet | medium | dense logic · coupling detected |
| Evaluator | Gemini 2.5 Flash | very low | end of Worker or Refactor session |
