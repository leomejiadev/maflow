# SPEC.md — Project Specification

> Agents: read at session start. Sections 1–3: user. Sections 4–6: Architect.

---

## 1. Project identity
> 👤 Fill this — one sentence per field.

- **Name:** [project-name]
- **Purpose:** [What problem does this solve?]
- **Target user:** [Who uses this?]
- **Complexity:** [simple / medium / complex]

---

## 2. Scope
> 👤 Fill this — max 5 items each.

### Core features
- [Feature 1]
- [Feature 2]
- [Feature 3]

### Out of scope
- [Non-goal 1]
- [Non-goal 2]

---

## 3. Stack
> 👤 Fill what you know — leave blank what you're unsure about.

- **Language:** [e.g. Python 3.12]
- **Framework:** [e.g. FastAPI]
- **Database:** [e.g. PostgreSQL]
- **ORM / ODM:** [e.g. SQLModel]
- **Auth:** [e.g. JWT / OAuth2]
- **AI layer:** [e.g. LangChain · OpenAI API · RAG — or N/A]
- **Infra:** [e.g. Docker · Railway · AWS]
- **Testing:** [e.g. pytest · TDD]

---

## 4. Architecture summary
> 🤖 Architect fills this. Full details in ARCHITECTURE.md.

- **Pattern:** [Architect defines]
- **Layers:** [Architect defines]
- **Key constraint:** [Architect defines]

---

## 5. Decisions already made
> 🤖 Architect fills this. Full context in decisions.md.

- [Decision 1]
- [Decision 2]

---

## 6. Dependencies
> 🤖 Architect fills this.
> Rule: use exact pinned versions. Write pyproject.toml directly — do not just list packages here.

### Install command
```bash
uv add [package==version] [package==version]
```

### pyproject.toml dependencies block
```toml
[project]
dependencies = [
    # Architect fills with exact versions
]

[project.optional-dependencies]
dev = [
    # Architect fills with exact dev versions
]
```

### Docker services required
```yaml
# paste docker-compose.yml services block — or N/A
```

### Environment variables
```
# VAR_NAME=description — or N/A
```

---

## 7. Current status
> Agent rule: update this section before closing every session.

- **Phase:** [e.g. Phase 1 — Architecture design]
- **Last session summary:** [One line]
- **Next task:** [One line]