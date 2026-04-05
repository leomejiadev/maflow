# GUIDE.md — Guía práctica maflow

## Instalación (una sola vez)

```bash
# 1. Clonar el repo
git clone https://github.com/leomejiadev/maflow.git

# 2. Instalar el auditor
cd maflow
uv pip install -e .
maflow --help       # verifica que funciona

# 3. Instalar cn (Continue CLI)
npm i -g @continuedev/cli
cn --version        # verifica que funciona
```

---

## Setup de un proyecto nuevo

```bash
# Copiás los templates a tu proyecto
cp -r maflow/templates/* tu-proyecto/
cp -r maflow/.continue tu-proyecto/
cp maflow/orchestrator.py tu-proyecto/

# Abrís tu proyecto en VSCode/Cursor
# Continue.dev carga .continue/config.yaml automáticamente
```

---

## El workflow en 4 pasos

### Paso 1 — Vos llenás SPEC.md (5 minutos)

Abrís `SPEC.md` y completás las secciones marcadas con 👤:
- Nombre del proyecto
- Qué hace y qué NO hace
- Stack tecnológico
- Complejidad: simple / medium / complex

---

### Paso 2 — Arquitecto planifica

En Continue.dev seleccionás `Architect · Refactor (Sonnet)` y escribís:

```
You are the Architect. Read SPEC.md. Follow CLAUDE.md Role: Architect.
```

El Arquitecto:
- Te hace máximo 3 preguntas si algo no está claro
- Escribe `ARCHITECTURE.md` completo
- Llena `decisions.md` y `SPEC.md` secciones 4-6
- Corre el close protocol automáticamente

---

### Paso 3 — Vos revisás el plan (0 tokens)

Leés `ARCHITECTURE.md`. Si algo no cierra, decíselo al Arquitecto antes de continuar.
**Este es el único punto de control antes de que empiece el código.**

---

### Paso 4 — El orquestador hace el resto

```bash
python orchestrator.py --log agent-log.md --project .
```

El orquestador corre automáticamente:

```
Fase 2 → Worker implementa (Gemini Flash)
Fase 3 → 3 Evaluadores en paralelo (Gemini Flash)
Fase 4 → Refactor (Claude Sonnet)
Fase 5 → Testing (Gemini Flash)
Fase 5.5 → Re-evaluación en paralelo (Gemini Flash)
maflow report → audita después de cada fase
```

Se detiene solo si detecta 🚫 BLOCKED — ahí intervenís vos para resolver el bloqueo.

---

### Paso 5 — Vos revisás el resultado final (0 tokens)

Leés `agent-log.md` de arriba a abajo.
Cada `➡️ NEXT` debería estar completado o marcado N/A.

---

## Comandos del orquestador

```bash
# Correr pipeline completo desde donde quedó
python orchestrator.py --log agent-log.md --project .

# Empezar desde una fase específica
python orchestrator.py --log agent-log.md --project . --from-phase refactor

# Ver qué haría sin ejecutar nada (recomendado la primera vez)
python orchestrator.py --log agent-log.md --project . --dry-run
```

---

## Comandos del auditor

```bash
# Reporte completo con drift por sesión
maflow report --log agent-log.md

# Las peores sesiones por drift
maflow worst --log agent-log.md

# Historial con alertas
maflow sessions --log agent-log.md

# Sin escribir entry al log
maflow report --log agent-log.md --no-write
```

---

## Qué significa el reporte

```
drift 0.0x - 2.0x  ● verde    → sesión sana
drift 2.0x - 4.0x  ● amarillo → considerá rotar pronto
drift 4.0x+        ● rojo     → el orquestador debería haber rotado
```

---

## Decisiones importantes

Cuando el agente necesita decidir algo no trivial, pregunta:

```
Decision needed: [opción A] vs [opción B] — which?
```

Respondés. El agente registra la decisión en `decisions.md` automáticamente.

---

## Estructura de archivos

```
tu-proyecto/
├── .continue/
│   └── config.yaml       # reglas para Continue.dev
├── SPEC.md               # 👤 vos · 🤖 Arquitecto
├── CLAUDE.md             # reglas de agentes
├── ARCHITECTURE.md       # el Arquitecto lo escribe
├── agent-log.md          # historial de sesiones
├── decisions.md          # decisiones arquitectónicas
└── orchestrator.py       # automatiza fases 2-5.5
```

---

## Qué hacer cuando el auditor muestra rojo

El auditor te avisa que una sesión creció demasiado y cada mensaje cuesta mucho más que al principio. Son 3 pasos para resolverlo:

**Paso 1 — Ves el rojo**
```bash
maflow report --log agent-log.md
# muestra: ● rojo  Worker·Flash  drift 5.2x
```

**Paso 2 — Rotás la sesión**

Si el orquestador está corriendo:
```bash
Ctrl+C
```

Si estás en Continue.dev manualmente:
```
Session complete. Run close protocol now.
```

El agente escribe el entry en `agent-log.md` con exactamente dónde quedó.

**Paso 3 — Reiniciás limpio**
```bash
python orchestrator.py --log agent-log.md --project . --from-phase worker
```

El nuevo agente lee solo el último entry del log — arranca con contexto limpio, drift en 0. No perdés nada — el trabajo hecho queda en los archivos.

---

## Flujo completo

```
Vos → llenás SPEC.md (5 min)
Arquitecto → ARCHITECTURE.md + decisions.md
Vos → revisás el plan (0 tokens)
Orquestador → fases 2 a 5.5 automático
Vos → revisás agent-log.md (0 tokens)
```