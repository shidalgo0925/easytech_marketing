# EM+Acción / EasyMarketingOne — Roadmap unificado

**Principio rector:** Si no afinamos el contenido, solo automatizamos ruido.  
**Prioridad estratégica:** Completar **Fase E** (motor de conocimiento y valor) **antes** de escalar todos los canales de Fase D.

**Visión vNext:**

```
Educar → Generar confianza → Capturar leads → Nutrir prospectos → Convertir clientes
```

Antes EM+Acción solo publicaba. Ahora debe ser **motor de autoridad digital y generación de demanda** para EasyTech.

---

## Mapa de fases

| Fase | Nombre | Estado | Notas |
|------|--------|--------|-------|
| **A** | Seguridad y despliegue | ✅ | Motor en producción, Git, systemd |
| **B** | Operación | 🔄 | Cola editorial activa; leads y secretos pendientes |
| **C** | Plataforma dashboard | ✅ | Campañas, calendario UI, métricas, flyers |
| **E** | **Motor de conocimiento y valor** | ⏳ **Siguiente** | Antes de escalar D.4–D.8 |
| **D** | Conectores multicanal | 🔄 Parcial | LinkedIn + FB live; IG/Google/TikTok pendientes |
| **F** | EN1 + recomendaciones | 📋 | Tras E + leads validados (ex-Fase 3–4 plan maestro) |

> **Orden de ejecución recomendado:** A → B → C → **E** → D (completar) → F  
> D.1–D.3 pueden seguir en paralelo mientras arranca E; **no escalar** YouTube/TikTok/Ads masivos hasta E2–E4 operativos.

Detalle histórico del plan maestro Accio: `docs/ACCIO_MARKETING_ENGINE.md`

---

## Fase A — Seguridad ✅

- [x] Motor vivo en ArrozConPollo (`/opt/easytech_marketing`)
- [x] Git + `.gitignore` + push GitHub `shidalgo0925/easytech_marketing`
- [x] `deploy/systemd` + `crontab.example`
- [x] `docs/INSTALACION.md`
- [ ] Backup `.env` offline cifrado

---

## Fase B — Operación 🔄

- [x] Cola LinkedIn #4–#11 reestructurada (ver regla editorial actual abajo)
- [x] 3 posts LinkedIn publicados (#1–#3)
- [ ] Validar leads Odoo (origen guía vs scraper)
- [ ] Confirmar cron LinkedIn/Meta en logs
- [ ] Rotar secretos expuestos (Meta App Secret)

---

## Fase C — Plataforma ✅

- [x] Módulo campañas (`Marketing/accio/campaigns.json`)
- [x] Calendario editorial UI + `calendar.json`
- [x] Panel métricas (clicks, conversiones)
- [x] Biblioteca flyers en dashboard
- [x] Dashboard EM+Acción (design system, conectores, privacidad)

---

## Fase E — Motor de Conocimiento y Valor ⏳ PRIORITARIA

**Objetivo:** Que EM+Acción publique contenido útil, educativo y contextualizado — no solo publicidad.

### E1. Contexto empresarial configurable

| Campo | Ejemplo EasyTech |
|-------|------------------|
| Empresa | Easy Technology Services |
| Industria | Transformación Digital |
| País | Panamá |
| Público objetivo | PYMEs Panamá |
| Productos/Servicios | Odoo+FE, EN1, EPOSOne, EClassOne, EPayRoll, consultoría |
| Diferenciadores | Integración FE+ERP, diagnóstico gratis, implementación local |
| Problemas que resuelve | Procesos manuales, falta de integración, falta de indicadores |
| Tono | Profesional, cercano, educativo |
| Objetivos comerciales | Generar diagnósticos tecnológicos |

**UI objetivo:** Dashboard → Configuración → Contexto de Negocio

| Hoy | Gap |
|-----|-----|
| Contexto disperso en `docs/CONTEXTO.md`, `PROMPT_OPERADOR.md`, `.cursor/rules/` | Falta módulo editable en dashboard + `Marketing/accio/business_context.json` |

**Entregables:**

- [ ] `Marketing/accio/business_context.json` (schema + defaults EasyTech)
- [ ] API `GET/POST /accio/config/business-context`
- [ ] Pantalla en dashboard EM+Acción
- [ ] Inyectar contexto en generación de copy y prompts del operador

---

### E2. Base de conocimiento (Knowledge Base)

El motor debe aprender de documentos, web corporativa, casos de éxito, FAQs, servicios y roadmaps.

**Repositorio objetivo:**

```
Marketing/knowledge/
├── easytech.md
├── en1.md
├── eposone.md
├── eclassone.md
├── epayroll.md
├── odoo_fe.md
├── casos_exito.md
└── faqs.md
```

| Hoy | Gap |
|-----|-----|
| Flyers + borradores sueltos en `Marketing/LinkedIn/`, `Marketing/Facebook/` | No existe `Marketing/knowledge/` |
| Guía lead magnet: https://n8n.etsrv.site/guia/ | Sin indexación ni ingestión al motor |

**Entregables:**

- [ ] Crear `Marketing/knowledge/` con fichas por producto
- [ ] `Marketing/knowledge/manifest.json` (fuentes, tags, producto)
- [ ] Script ingestión: MD/PDF → chunks (fase 2: embeddings)
- [ ] API consulta contexto para generador de temas

---

### E3. Generador de temas (no posts aleatorios)

Estructura obligatoria por pieza:

```
Problema → Explicación → Solución → Recomendación
```

Ejemplo: *¿Por qué fracasan los proyectos ERP?* → errores comunes → consecuencias → buenas prácticas → checklist.

| Hoy | Gap |
|-----|-----|
| Posts manuales/agente en `content_queue.json` con buena estructura editorial | Sin generador automático ni plantilla enforced |
| Campo `content_type` (`valor` \| `venta`) | Sin campo `topic_framework` ni validación de estructura |

**Entregables:**

- [ ] Plantilla JSON post: `problem`, `explanation`, `solution`, `recommendation`
- [ ] Validador pre-publicación en `validate_flyers.py` o módulo nuevo
- [ ] Endpoint `POST /accio/content/generate-topic` (LLM + contexto E1 + KB E2)

---

### E4. Matriz de valor (distribución automática)

**Objetivo vNext (Fase E):**

| Tipo | % |
|------|---|
| Educación | 50% |
| Consejos | 20% |
| Casos reales | 15% |
| Tendencias | 10% |
| Venta directa | 5% |

**Regla:** 95% aportar valor · 5% vender.

**Regla actual (interina — Fase B):** 3 valor + 1 venta por bloque de 4 (**75% / 25%**).  
Implementada en `content_queue.json` → `content_type`: `valor` | `venta`.

| Hoy | Gap |
|-----|-----|
| `content_type` binario valor/venta | Ampliar a: `educacion`, `consejo`, `caso`, `tendencia`, `venta` |
| Calendario manual | Motor debe balancear % al encolar siguiente post |

**Entregables:**

- [ ] Ampliar `content_type` en cola y campañas
- [ ] Reglas de balanceo en `accio_engine` al proponer siguiente post
- [ ] Migrar cola pendiente de 75/25 → matriz 95/5 gradualmente

---

### E5. Generación inteligente de flyers

**Hoy:** Tema → flyer PNG estático (`Marketing/flyers/` + `manifest.json`).

**Objetivo:**

```
Contexto (E1) + KB (E2) + Tema (E3) + Objetivo (E4)
    → Copy → Título → Diseño → Flyer educativo (no banner publicitario)
```

Ejemplo: *IA para PYMEs* + objetivo *Educar* → checklist visual + CTA suave.

| Hoy | Gap |
|-----|-----|
| 11 flyers PNG manuales (#10 IIUS falta) | Sin pipeline generativo |
| Flyer obligatorio para LinkedIn/Meta ✅ | Sin templates dinámicos por tipo de valor |

**Entregables:**

- [ ] Templates HTML/SVG por tipo (educación, checklist, consejo, caso)
- [ ] Generador PNG (headless) o integración Canva/Figma API
- [ ] CTA suave configurable por matriz E4

---

### E6. Calendario editorial inteligente

**Objetivo:** El motor asigna tipo de contenido por día, manteniendo equilibrio E4.

| Día | Tipo sugerido |
|-----|---------------|
| Lunes | Consejo |
| Miércoles | Caso real |
| Viernes | Tendencia |
| Domingo | Venta (único slot comercial semanal) |

| Hoy | Gap |
|-----|-----|
| `calendar.json` + fechas fijas Mar/Jue/Vie 13:00 PA | Sin lógica día→tipo |
| Cron LinkedIn/Meta separados | Sin orquestador que elija post según matriz |

**Entregables:**

- [ ] Reglas `editorial_rules.json` (día, tipo, canal, peso)
- [ ] Job semanal: generar/revisar calendario desde matriz E4
- [ ] Dashboard: vista semanal por tipo de valor

---

### E7. Biblioteca de valor ETS (lead magnets)

Activos reutilizables para captura y nutrición:

- Checklists · Guías · Plantillas · Infografías · Mini cursos · Whitepapers

Flujo: **Lead magnet → landing → CRM (Odoo) → nutrición**

| Hoy | Gap |
|-----|-----|
| Guía FE Panamá (`/guia/`) ✅ | Una sola pieza |
| Posts enlazan guía en first_comment | Sin biblioteca estructurada |

**Entregables:**

- [ ] `Marketing/lead_magnets/` (PDF/MD + metadata)
- [ ] Catálogo en dashboard + UTM por magnet
- [ ] Primeros activos: *10 errores al implementar ERP*, *Checklist FE Panamá*, *Diagnóstico PYME*
- [ ] Integración Odoo: tag origen + secuencia nutrición

---

### Criterio de éxito Fase E

- [ ] Contexto negocio editable sin tocar código
- [ ] KB con ≥6 fichas producto + casos de éxito
- [ ] Nuevo post generado sigue Problema→Recomendación
- [ ] Cola respeta matriz 95/5 en ventana de 20 posts
- [ ] ≥1 lead magnet nuevo capturando en Odoo
- [ ] Flyer educativo generado (no solo PNG estático de catálogo)

---

## Fase D — Conectores multicanal 🔄

Estrategia: **estructura primero, APIs después** (`docs/ARQUITECTURA_CONECTORES.md`).  
**Pausa de escalado:** completar E2–E4 antes de activar cron masivo en YouTube/TikTok/Ads.

| # | Canal | Estado | OAuth / Publisher |
|---|-------|--------|-------------------|
| D.1 | LinkedIn | ✅ live | https://n8n.etsrv.site/linkedin/ |
| D.2 | Facebook Page | ✅ live | https://n8n.etsrv.site/meta/ |
| D.3 | Instagram | ⏳ | OAuth Meta; falta `META_IG_USER_ID` |
| D.4 | Google Business | ⏳ | https://n8n.etsrv.site/google/ |
| D.5 | YouTube | stub | OAuth Google compartido |
| D.6 | TikTok | stub | https://n8n.etsrv.site/tiktok/ |
| D.7 | Meta Ads | stub | — |
| D.8 | Google Ads | stub | — |

Registro: `Marketing/accio/connectors.json` · Guía: `docs/CONECTAR_REDES.md`

**Después de Fase E:** republicar cola FB/IG/Google con copy generado desde KB, no catálogo de productos repetido.

---

## Fase F — EN1 y recomendaciones comerciales 📋

Consolida ex-Fase 3–4 del plan maestro (`ACCIO_MARKETING_ENGINE.md`).

- [ ] `en1_sync.py` — lead → EN1 pipeline
- [ ] Reglas enrutamiento: EN1 vs Odoo vs ambos
- [ ] Scoring prospectos (scraper + señales FE/sector)
- [ ] Recomendaciones: qué vender, a quién, qué campaña (inputs: Odoo + métricas + E7)

---

## Reglas editoriales — resumen

| Versión | Regla | Dónde |
|---------|-------|-------|
| **Actual (B)** | 3 valor + 1 venta (75/25) | `content_queue.json`, `CALENDARIO_PUBLICACION.md` |
| **Objetivo (E)** | Matriz 95/5 por tipo | E4 + E6 |

La cola jun–jul 2026 ya usa `valor`/`venta` con copy educativo. Al cerrar E4, migrar tipos y rebalancear.

---

## Referencias

| Doc | Contenido |
|-----|-----------|
| [CONTEXTO.md](CONTEXTO.md) | Estado operativo del sistema |
| [ACCIO_MARKETING_ENGINE.md](ACCIO_MARKETING_ENGINE.md) | Visión Accio cerebro + brazos |
| [CONECTAR_REDES.md](CONECTAR_REDES.md) | OAuth por canal |
| [CALENDARIO_PUBLICACION.md](../Marketing/CALENDARIO_PUBLICACION.md) | Cola actual |
| [PROMPT_OPERADOR.md](../Marketing/accio/PROMPT_OPERADOR.md) | Prompt agente Accio |

**Actualizado:** 2026-06-20
