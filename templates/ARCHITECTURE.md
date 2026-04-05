# ARCHITECTURE.md — Project Architecture

> Who writes: Architect only.
> Who reads: Worker · Refactor.
> Must be complete before any Worker session starts.

---

## 1. Pattern

- **Pattern:** [e.g. Layered · Hexagonal · Modular monolith]
- **Complexity:** [simple / medium / complex — matches SPEC.md]
- **Justification:** [one sentence]

---

## 2. Layers, contracts and naming

> Define every layer. One block per layer.

### Layer: [Name]
- **Responsibility:** [one sentence]
- **Can import from:** [layer names]
- **Cannot import from:** [layer names]
- **File pattern:** `app/[folder]/{entity}_[suffix].py`
- **Class pattern:** `{Entity}[Suffix]`

> Repeat for every layer.

---

## 3. Dependency flow

```
[Layer] → [Layer] → [Layer]
```

Rule: one direction only. If A imports B, B never imports A.

---

## 4. Folder structure

```
app/
├── [folder]/
│   └── {entity}_[suffix].py
└── main.py

tests/
└── [folder]/
    └── test_{entity}_[suffix].py
```

---

## 5. Key contracts

1. [e.g. Services never import from Endpoints]
2. [e.g. Repositories are the only layer allowed to access the database]
3. [e.g. All business logic lives in Services]

---

## 6. External integrations

> Fill only if applicable — leave blank otherwise.

- **AI / LLM layer:** [or N/A]
- **External APIs:** [or N/A]
- **Background tasks:** [or N/A]
- **Cache:** [or N/A]
