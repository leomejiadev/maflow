# ARCHITECTURE.md — Project Architecture

> **Who writes this:** Architect agent only.
> **Who reads this:** Worker agent · Refactor agent.
> **Token rule:** This file must be complete before any Worker session starts.
> The Worker implements against this document — never invents structure.

---

## 1. Pattern

- **Pattern:** [e.g. Layered · Hexagonal · Modular monolith]
- **Justification:** [Why this pattern fits this project scope and complexity]
- **Complexity level:** [simple / medium / complex — must match SPEC.md section 1]

---

## 2. Layer definitions

> Define every layer. For each one: responsibility, allowed imports, forbidden imports.

### Layer: [Name]
- **Responsibility:** [What this layer does — one sentence]
- **Can import from:** [Layer names]
- **Cannot import from:** [Layer names]
- **File pattern:** `app/[folder]/{entity}_[suffix].py`

### Layer: [Name]
- **Responsibility:**
- **Can import from:**
- **Cannot import from:**
- **File pattern:**

> Repeat for every layer in the architecture.

---

## 3. Dependency flow

> Show the allowed direction of dependencies in one line.
> Example: Endpoints → Schemas → Dependencies → Services → Repositories → Models

```
[Layer] → [Layer] → [Layer]
```

> Rule: dependencies flow in ONE direction only.
> If layer A imports from layer B, layer B must never import from layer A.

---

## 4. Folder structure

> Complete folder tree as the Worker must create it.
> No ambiguity — every folder and file pattern defined here.

```
app/
├── [folder]/
│   ├── __init__.py
│   └── {entity}_[suffix].py
├── [folder]/
│   ├── __init__.py
│   └── {entity}_[suffix].py
├── core/
│   ├── config.py
│   └── database.py
└── main.py

tests/
├── [folder]/
│   └── test_{entity}_[suffix].py
└── conftest.py
```

---

## 5. Naming conventions

> Worker must follow these exactly. No exceptions.

| Layer | File pattern | Class pattern | Example |
|---|---|---|---|
| [Layer] | `{entity}_[suffix].py` | `{Entity}[Suffix]` | `user_service.py → UserService` |
| [Layer] | `{entity}_[suffix].py` | `{Entity}[Suffix]` | `user_repository.py → UserRepository` |

---

## 6. Key contracts

> The non-negotiable rules between layers.
> Worker must never violate these — Refactor agent checks for violations.

1. [Contract 1 — e.g. Services never import from Endpoints]
2. [Contract 2 — e.g. Repositories are the only layer allowed to access the database]
3. [Contract 3 — e.g. All business logic lives in Services — never in Endpoints or Repositories]
4. [Contract 4 — e.g. Schemas define all input/output shapes — no raw dicts across layers]

---

## 7. External integrations

> Only fill if the project has AI layer, third party APIs or async workers.
> Leave blank if not applicable.

- **AI / LLM layer:** [e.g. LangChain · how it connects to Services layer]
- **External APIs:** [e.g. Stripe · which layer handles the integration]
- **Background tasks:** [e.g. Celery · where workers live in the folder structure]
- **Cache:** [e.g. Redis · which layer owns cache logic]
