# ACCIO Marketing Engine — Plan maestro

**Objetivo:** Accio = Director de Marketing Autónomo de EasyTech  
**Servidor:** ArrozConPollo (`95.111.244.137`)  
**Estado:** Fase 0 (infra) desplegada · Fase 1+ pendiente (cerebro Accio)

---

## Por qué se desvió la conversación

Al auditar ArrozConPollo encontramos **piezas sueltas sin cerebro**. La pregunta natural fue *"¿qué hay?"* y eso llevó a hablar de **reemplazo** (Cursor, scripts Python) en lugar de **orquestación** (Accio como operador).

Eso fue un error de encuadre, no un cambio de estrategia.

| Lo que pareció | Lo que en realidad pasó |
|----------------|-------------------------|
| "Abandonemos Accio" | No — falta conectar Accio al stack |
| "Cursor es el motor" | Cursor **construyó los brazos** mientras Accio no tenía paso 2 |
| "Odoo reemplaza EN1" | No — Odoo es CRM hoy; EN1 es destino comercial del plan |

---

## Visión original (la que retomamos)

```
ACCIO (Director de Marketing)
        │
        ├─ Detecta oportunidades
        ├─ Genera contenido / campañas
        ├─ Publica (LinkedIn, FB, IG, blog)
        ├─ Capta leads
        ├─ Alimenta EN1 + pipeline
        └─ Recomienda acciones comerciales
```

**Productos bajo gestión de Accio:**

- EPOSOne · EN1 · EPayRoll · EClassOne · Servicios EasyTech

**Principio:** tú no operas marketing manualmente ni dependes de Cursor para cada post.

---

## Arquitectura objetivo

```
┌─────────────────────────────────────────────────────────────┐
│  ACCIO — Cerebro (IA + reglas + calendario estratégico)     │
│  · Prospectar · Oportunidades · Copy · Campañas · KPIs      │
└───────────────────────────┬─────────────────────────────────┘
                            │ API / cola de órdenes
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  ORQUESTADOR (Motor Accio en ArrozConPollo)  ← FALTA       │
│  accio_engine — recibe órdenes, ejecuta, reporta           │
└───┬─────────┬─────────┬─────────┬─────────┬─────────────────┘
    │         │         │         │         │
    ▼         ▼         ▼         ▼         ▼
 scraper   publisher  lead_api    n8n     en1_sync
    │         │         │         │         │
    └─────────┴────Odoo CRM───────┴────EN1 CRM──────────────►
```

**Lo desplegado hoy = capa de ejecución (brazos).**  
**Lo pendiente = Orquestador Accio (cerebro conectado).**

---

## Mapa: visión ↔ lo que ya existe

| Responsabilidad Accio | Herramienta hoy | Estado | Gap |
|----------------------|-----------------|--------|-----|
| Prospectar empresas | `scraper_panama.py` | ✅ Script | Accio no lo dispara ni interpreta resultados |
| Detectar oportunidades | — | ❌ | Falta módulo scoring + señales (FE, Odoo, sector) |
| Generar calendario editorial | `CALENDARIO_PUBLICACION.md` | ⚠️ Manual | Accio debe escribir → `content_queue.json` |
| Crear contenido | Flyers + borradores MD | ✅ Assets | Accio no genera solo ni llena cola |
| Publicar LinkedIn | `linkedin_publisher.py` | ✅ 3 posts | Accio no controla ciclo completo |
| Publicar FB / IG / blog | Borradores MD | ❌ API | Sin integración Meta / blog |
| Captar leads | Landing + `lead_api.py` | ✅ | OK inbound |
| Alimentar CRM | `odoo_sync.py` + Odoo | ✅ Parcial | Sin EN1 |
| Seguimiento comercial | Odoo pipeline | ⚠️ Manual | Sin EN1 + sin WhatsApp/Econverso |
| Monitorear resultados | `publish_log.json` | ⚠️ Básico | Falta dashboard / KPIs para Accio |
| Recomendar acciones | — | ❌ | Fase 4 |

---

## Roadmap ACCIO Marketing Engine

### Fase 0 — Infraestructura (HECHO)

- [x] VPS preparado (Docker, Python, `/opt/easytech_marketing`)
- [x] Scraper → CSV
- [x] Odoo sync + Lead API
- [x] LinkedIn OAuth + publisher
- [x] n8n + landing guía + flyers
- [x] Cron domingo (scraper + Odoo)

**Conclusión Fase 0:** los brazos existen. Accio aún no los dirige.

---

### Fase 1 — Accio genera (Director creativo)

**Objetivo:** Accio produce sin Cursor manual.

| Entregable | Destino en servidor |
|------------|---------------------|
| Calendario editorial 4 semanas | `Marketing/accio/calendar.json` |
| Posts LinkedIn #5–#12 | `Marketing/content_queue.json` |
| Campañas por producto | `Marketing/accio/campaigns/` |
| Lista prospectos objetivo | `Marketing/accio/targets.json` |

**Implementación técnica (Fase 1 — INICIADA 2026-06-19):**

1. ✅ `Motor_Tecnico/accio_engine/` — API REST en puerto 8092
2. ✅ `systemctl easytech-accio-engine` + nginx `/accio/`
3. ✅ Cola órdenes: `Marketing/accio/orders.json`
4. ✅ Cron tick cada 15 min
5. 📖 API: `docs/ACCIO_API.md`

Accio envía órdenes vía `POST https://n8n.etsrv.site/accio/...` con `ACCIO_API_KEY`.

**Criterio de éxito:** nueva semana de contenido sin abrir Cursor.

---

### Fase 2 — Accio controla canales

**Objetivo:** publicación multi-canal autónoma.

| Canal | Estado | Acción |
|-------|--------|--------|
| LinkedIn | ✅ Publisher | Conectar a orquestador + métricas |
| Instagram / Facebook | ❌ | Meta API o publicación asistida |
| Blog | ❌ | WordPress/EN1 blog endpoint |
| n8n | ⚠️ | Workflows como timers del orquestador |

**Criterio de éxito:** Accio dispara publicación; tú solo apruebas excepciones (opcional).

---

### Fase 3 — Accio alimenta EN1

**Objetivo:** lead → EN1 pipeline comercial (no solo Odoo).

```
Lead (landing / LinkedIn / scraper)
        → Orquestador Accio (clasifica producto)
        → EN1 CRM (demo EN1 / EPOS / EClass / EPayRoll)
        → Odoo (contabilidad / ERP si aplica)
```

**Requisitos de negocio (bloqueantes):**

- URL API EN1 + credenciales
- Modelo de lead en EN1 (campos, etapas)
- Reglas: qué lead va a EN1 vs Odoo vs ambos

**Implementación:** `Motor_Tecnico/en1_sync.py` llamado por orquestador.

---

### Fase 4 — Accio recomienda

**Objetivo:** inteligencia comercial.

- Qué vender (producto × sector)
- A quién vender (scoring prospectos)
- Qué campaña lanzar (basado en KPIs)
- Alertas: "FE + retail Panamá — lanzar campaña #3"

**Inputs:** Odoo + EN1 + métricas redes + scraper.

---

## Rol de cada actor (definitivo)

| Actor | Rol | NO es |
|-------|-----|-------|
| **Accio** | Director: decide qué, cuándo, a quién | El servidor ni un script suelto |
| **Orquestador** (`accio_engine`) | Ejecuta órdenes de Accio en ArrozConPollo | Reemplazo de Accio |
| **Cursor** | Ingeniería puntual (integrar EN1, bugs) | Operador diario de marketing |
| **Tú** | Aprobación estratégica + cierre ventas | Copywriter / publicador manual |
| **Odoo** | CRM ERP hoy | EN1 (futuro: dual o sync) |
| **EN1** | CRM comercial productos SaaS | Destino Fase 3 |

---

## Trabajo pendiente real (priorizado)

### Inmediato (esta semana)

1. **Definir Accio técnicamente:** ¿agente en n8n + LLM, API propia, o agente externo que escribe JSON al servidor?
2. **Crear `accio_engine`** — capa mínima que lea/escriba `content_queue.json` y dispare publisher/scraper.
3. **Accio genera posts #5–#12** → orquestador los encola (sin Cursor en el loop).
4. **Credenciales EN1** — desbloquear Fase 3.

### Corto plazo (2–4 semanas)

5. Importar workflows n8n como reloj del orquestador.
6. Módulo oportunidades (scoring sobre CSV + señales Panamá FE).
7. `en1_sync.py` + reglas de enrutamiento lead.

### Medio plazo

8. Meta API (IG/FB).
9. Dashboard KPIs para Accio.
10. Recomendaciones Fase 4.

---

## Pregunta correcta (retomada)

> **¿Cómo convertimos Accio en el operador principal usando lo que ya existe?**

**Respuesta:**

1. **No tirar** scraper, publisher, lead API, n8n, Odoo.
2. **Agregar** `accio_engine` como cerebro conectado.
3. **Accio** deja de ser solo chat → pasa a **emitir planes y órdenes** al orquestador.
4. **Cursor** solo entra para construir integraciones (EN1, Meta), no para operar campañas.
5. **Tú** supervisas KPIs y cierras; no publicas ni copias posts.

---

## Próximo paso concreto

Decidir **dónde vive el cerebro Accio**:

| Opción | Pros | Contras |
|--------|------|---------|
| **A. Agente Accio externo → API en VPS** | Accio sigue siendo "Accio" | Necesita API estable |
| **B. n8n + nodo IA como Accio** | Ya hay n8n | Menos flexible para estrategia |
| **C. `accio_engine.py` + LLM en VPS** | 100% autónomo en ArrozConPollo | Costo LLM / Ollama |

**Recomendación:** Opción **A + C** — orquestador en VPS; Accio (agente) envía planes vía API/archivos; el VPS ejecuta 24/7 sin Cursor.

---

## Referencias

- Inventario actual: `docs/INVENTARIO_DESPLIEGUE.md`
- Cola publicación: `Marketing/content_queue.json`
- Flyers: `Marketing/flyers/manifest.json`
- LinkedIn: `docs/LINKEDIN_AUTOMATIZACION.md`
