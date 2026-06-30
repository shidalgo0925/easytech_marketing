# Plan Maestro EM+Acción / Marketing OS

**Versión:** 3.0  
**Estado:** Propuesta estratégica (GO pendiente)  
**Producto:** EM+Acción (EasyMarketingOne) · Easy Technology Services  
**Objetivo:** Construir el primer **Marketing Operating System** de Easy Technology Services.

**Jerarquía documental:**

```
Constitución → Product Vision v2.2 (congelada) → Plan Maestro v3 → ROADMAP → Código
```

| Documento | Rol |
|-----------|-----|
| [EMACCION_PRODUCT_VISION_v2.2.md](EMACCION_PRODUCT_VISION_v2.2.md) | Visión de producto (inmutable) |
| **Este documento** | Estrategia de fases A–P y prioridad de mercado |
| [ROADMAP.md](ROADMAP.md) | Sprints técnicos M0–M13 + seguimiento operativo |
| [MARKETING_OS_MIGRATION_PLAN.md](MARKETING_OS_MIGRATION_PLAN.md) | Migración legacy → plataforma |

**Supersede en prioridad estratégica:** [EMACCION_V2_PLAN_MAESTRO.md](EMACCION_V2_PLAN_MAESTRO.md) v2.0 (referencia histórica).

---

## Visión

EM+Acción **no** es un publicador.  
EM+Acción **no** es un CRM.  
EM+Acción **no** es una herramienta de IA.

EM+Acción es el **cerebro comercial** de toda la empresa.

Debe ser capaz de:

1. Entender la empresa
2. Detectar oportunidades
3. Planificar
4. Crear estrategias
5. Generar contenido
6. Ejecutar campañas
7. Medir resultados
8. Aprender continuamente

---

## Arquitectura general

```
                 EMPRESA
                    │
            Corporate Memory          (M1)
                    │
             Company Brain            (M2)
                    │
        Marketing Knowledge Base      (M3–M9)
                    │
             Decision Engine          (M10)
                    │
            Marketing Brain IA        (M11)
                    │
        Opportunity Engine            (Fase F / post-M11)
                    │
          Marketing Planner           (VS1 + Plan Engine)
                    │
         Campaign Generator           (Fase H)
                    │
        Content Generator IA          (Fase I + M8)
                    │
         Approval Workflow            (M10.5)
                    │
        Automation Engine             (M13)
                    │
    LinkedIn · Facebook · Instagram · Google · Email · WhatsApp · Blog · Landings
                    │
             Analytics Engine         (M12 / Fase M)
                    │
            Learning Engine           (Fase N)
                    │
              Company Brain           (loop)
```

El sistema forma un **ciclo cerrado**: aprende de sus resultados y mejora sus decisiones.

---

## Roadmap por fases

### Fase A — Fundación

**Objetivo:** Crear la base técnica.  
**Estado:** ✅ casi terminada (~90%).

Incluye: arquitectura · multi-tenant · API · seguridad · base de datos · configuración.

**Código:** Plan V2 fases A–C · `platform_infrastructure/` · `auth.db` · nginx/systemd.

---

### Fase B — Knowledge Layer

**Objetivo:** Que el sistema conozca completamente la empresa.  
**Estado:** ≈80% (M0–M9 en código; migración prod pendiente).

| Componente | Módulo |
|------------|--------|
| Corporate Memory | M1 |
| Company Brain | M2 |
| Marcas | M3 |
| Publicaciones | M4 |
| Productos y servicios | M5 |
| Knowledge articles | M6 |
| Campañas | M7 |
| Flyers / assets | M8 |
| Leads | M9 |
| Competidores, casos, FAQs | Parcial (KB + Brain) |

---

### Fase C — Decision Engine

**Objetivo:** Convertir conocimiento en decisiones.  
**Estado:** ≈90% (M10.1–M10.4 ✅ · M10.5 pendiente).

| Componente | Sub-fase |
|------------|----------|
| Rules Engine | M10.1 |
| Priority Engine | M10.2 |
| Recommendation Engine | M10.3 |
| Daily Roadmap | M10.4 |
| Approval Queue | M10.5 |

**Sin IA en M10** — reglas deterministas primero.

---

### Fase D — AI Layer

**Prioridad:** 🔴 máxima (gate de M11 y asistente).

**Objetivo:** Toda la inteligencia pasa por un **único punto**.

**AI Provider Manager** debe soportar:

- Ollama
- LiteLLM
- OpenAI
- OpenRouter
- Anthropic
- Gemini

```
AI Request
    ↓
Provider Manager
    ↓
Proveedor seleccionado
    ↓
Respuesta normalizada
```

**V1 producción ETS:** LiteLLM en CODITO → Ollama (`qwen2.5-coder`).

---

### Fase E — Marketing Brain

**Objetivo:** Que la IA piense como un **Director de Marketing** (M11).

Debe responder:

- ¿Qué producto impulsar?
- ¿Qué campaña conviene?
- ¿Qué publicar?
- ¿Qué CTA usar?
- ¿Qué imagen?
- ¿Qué horario?
- ¿Qué red social?

**No reemplaza** Recommendation / DailyRoadmap — enriquece `reason`, `description`, `confidence`.

---

### Fase F — Opportunity Engine

**Aquí comienza el verdadero negocio** — inmediatamente después de Marketing Brain.

Debe detectar automáticamente:

- Clientes sin seguimiento
- Productos olvidados
- Marcas sin publicaciones
- Campañas detenidas
- Servicios con alta demanda
- Competidores activos
- Eventos próximos
- Estacionalidad
- Noticias relevantes
- Cambios regulatorios

Todo se convierte en **oportunidades** accionables (input del Decision Engine + Brain).

---

### Fase G — Marketing Planner

La IA crea automáticamente: objetivos · KPIs · calendario · embudos · presupuesto · canales · público.

**Hoy:** Vertical Slice 1 (`MarketingPlan` v1.1) — base del planner.

---

### Fase H — Campaign Engine ✅ (2026-06-30)

Recomendación aprobada → campaña estructurada con explain. Ver `docs/CAMPAIGN_ENGINE.md`.

```
Campaña → Objetivo → Audiencia → Canales → KPIs → (futuro) Contenido → Publisher
```

---

### Fase I — Content Engine

Genera: posts · artículos · carruseles · videos · emails · WhatsApp · landings · scripts · presentaciones.

---

### Fase J — Approval Workflow

**Nada sale automáticamente.**

```
IA → Revisión humana → Aprobado → Publicar
```

M10.5 en código. Publicación 100% automática = futuro, tras confianza operativa.

---

### Fase K — Automation Engine (M13)

**Automation Brain** — decide y ejecuta:

- ¿Publico? ¿Espero? ¿Cambio imagen? ¿Cambio CTA?
- ¿Creo campaña? ¿Envío correo? ¿Creo tarea CRM?

Ya no solo recomendar — **actuar** (post-aprobación).

---

### Fase L — Connectors

LinkedIn · Meta · Instagram · Google Ads · Google Business · YouTube · TikTok · WordPress · WhatsApp · Odoo · EN1 · HubSpot · Mailchimp · n8n · Webhooks · API REST.

---

### Fase M — Analytics

Dashboard ejecutivo: ROI · leads · conversiones · CTR · CPL · CPA · ventas · embudos · redes · campañas · comparativos.

**Slice plataforma:** M12 Business Intelligence (unifica Analytics + preguntas gerenciales).

---

### Fase N — Learning Engine

La IA aprende qué CTA, imagen, horario, producto y sector funcionan.  
Toda esa información vuelve al **Company Brain**.

---

### Fase O — Business Intelligence

Tableros para gerencia. Responder:

- ¿Qué está pasando?
- ¿Por qué pasó?
- ¿Qué debo hacer?
- ¿Qué pasará el próximo mes?

---

### Fase P — Marketing Operating System

Versión final — ciclo completo:

```
Observar → Entender → Analizar → Descubrir oportunidades → Planificar → Crear
→ Aprobar → Ejecutar → Medir → Aprender → Mejorar → Repetir
```

---

## Mapeo Plan Maestro ↔ Marketing OS (código)

| Plan Maestro | Marketing OS / V2 |
|--------------|-------------------|
| Fase B Knowledge | M0–M9 |
| Fase C Decision | M10 |
| Fase D AI Layer | AI Provider Manager (transversal) |
| Fase E Brain | M11 |
| Fase F Opportunity | Opportunity Engine + **Marketing Intelligence Layer** (scorer, composer, explain) |
| Fase J Approval | M10.5 |
| Fase K Automation | M13 Automation Brain |
| Fase M + O | M12 Business Intelligence |

**Regla:** no re-arquitecturar M0–M11; extender con M12/M13 y reordenar GO.

---

## Prioridad inmediata (próximos sprints)

| Prioridad | Trabajo | Estado |
|-----------|---------|--------|
| 🔴 1 | Migrar M4–M9 a producción y activar `marketing_os.db` | Pendiente |
| 🔴 2 | Configurar `ACCIO_*_STORE=dual` y reiniciar servicio | Pendiente |
| 🔴 3 | Implementar **M10.5** Approval Queue | Pendiente |
| 🔴 4 | Implementar **AI Provider Manager** (LiteLLM/CODITO → Ollama) | Pendiente |
| 🔴 5 | Implementar **M11** Marketing Brain | Pendiente |
| 🟠 6 | Completar matriz de conocimiento (Knowledge Engine) | Pendiente |
| 🟠 7 | Desarrollar **Opportunity Engine** + Intelligence Layer | ✅ código |
| 🟡 8 | Completar Workspace/Console unificado | Pendiente |
| 🟡 9 | Analytics + **M12** Business Intelligence | Pendiente |
| 🟢 10 | Learning continuo + **M13** automatización avanzada | Futuro |

---

## Objetivo final

Que EM+Acción se convierta en el **centro de inteligencia comercial** de Easy Technology Services y, posteriormente, en un **producto SaaS** comercializable, donde la IA no solo genere contenido, sino que **comprenda el negocio**, **tome decisiones fundamentadas** y **mejore continuamente** con base en resultados.

---

## Referencias

- [ROADMAP.md](ROADMAP.md) — sprints y estado código
- [MARKETING_OS_SPRINT12_DECISION_ENGINE.md](MARKETING_OS_SPRINT12_DECISION_ENGINE.md)
- [EMACCION_CONTEXTO_OPERATIVO.md](EMACCION_CONTEXTO_OPERATIVO.md)
- [ACCIO_AI_PROVIDER_MANAGER.md](ACCIO_AI_PROVIDER_MANAGER.md)
