# EM+Acción V2 — Roadmap operativo

**Producto:** EM+Acción (EasyMarketingOne)

## Jerarquía documental — orden de lectura

```
Constitución  →  Product Vision  →  Domain Model  →  Arquitectura  →  Roadmap  →  Código
(inmutable)      (qué es)           (objetos)        (cómo)           (cuándo)     (impl)
```

| # | Capa | Documento | Estado |
|---|------|-----------|--------|
| 1 | **Constitución** | [MARKETING_OS_CONSTITUTION.md](MARKETING_OS_CONSTITUTION.md) v1.0 | ✅ |
| 2 | **Product Vision** | [EMACCION_PRODUCT_VISION_v2.2.md](EMACCION_PRODUCT_VISION_v2.2.md) | CONGELADO |
| 3 | **Domain Model** | [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) | ✅ v1.0 |
| 4 | **Arquitectura** | [MARKETING_OS_ARCHITECTURE.md](MARKETING_OS_ARCHITECTURE.md) | ✅ v1.0 |
| 5 | **Roadmap** | Este documento · Sprints | Activo |
| 6 | **Código** | `Motor_Tecnico/` | Sprint 3+ (GO por fase) |

**Regla:** fase conceptual **cerrada** tras commit Constitución. Solo entregables técnicos verificables por sprint.

**Plan maestro:** [EMACCION_V2_PLAN_MAESTRO.md](EMACCION_V2_PLAN_MAESTRO.md) *(alineación pendiente — capa 4)*  
**Estado vs código:** [EMACCION_V2_ESTADO.md](EMACCION_V2_ESTADO.md)  
**Contexto operativo:** [EMACCION_CONTEXTO_OPERATIVO.md](EMACCION_CONTEXTO_OPERATIVO.md)  
**Regla:** **No implementar una fase hasta cerrar completamente la anterior.**  
**Runtime:** requiere **GO explícito** por fase.

**Actualizado:** 2026-06-29 · **M3 Brands** ✅ · **Siguiente:** M4 Publications (GO)

**Forma de trabajo:** no más docs de visión · no redefinir producto · entregables verificables por sprint · Principio 19 antes de codear.

---

## Sprint 0 — Arquitectura del dominio ✅

**Spec:** [MARKETING_OS_DOMAIN_SPRINT0.md](MARKETING_OS_DOMAIN_SPRINT0.md) · **ADR:** [adr/0001-marketing-os-domain-sprint0.md](adr/0001-marketing-os-domain-sprint0.md)

---

## Sprint 1 — Domain Model + BD conceptual ✅

**Spec:** [MARKETING_OS_SPRINT1_DOMAIN_MODEL.md](MARKETING_OS_SPRINT1_DOMAIN_MODEL.md) — cerrado 2026-06-26

| Entregable | Doc | Estado |
|------------|-----|--------|
| Domain Model v1.0 | [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) | ✅ |
| BD conceptual + DDL | [MARKETING_OS_DOMAIN_PERSISTENCE.md](MARKETING_OS_DOMAIN_PERSISTENCE.md) | ✅ |
| Eventos v1.0 | [MARKETING_OS_DOMAIN_EVENTS.md](MARKETING_OS_DOMAIN_EVENTS.md) | ✅ |
| Servicios dominio | [MARKETING_OS_DOMAIN_SERVICES.md](MARKETING_OS_DOMAIN_SERVICES.md) | ✅ |
| Glosario v1.0 | [MARKETING_OS_GLOSSARY.md](MARKETING_OS_GLOSSARY.md) | ✅ |
| ADR persistencia | [adr/0002-marketing-os-persistence-store.md](adr/0002-marketing-os-persistence-store.md) | ✅ |

---

## Sprint 2 — Arquitectura de implementación ✅

**Spec:** [MARKETING_OS_SPRINT2_ARCHITECTURE.md](MARKETING_OS_SPRINT2_ARCHITECTURE.md) — cerrado 2026-06-26

| Entregable | Doc | Estado |
|------------|-----|--------|
| Capas + módulos | [MARKETING_OS_ARCHITECTURE.md](MARKETING_OS_ARCHITECTURE.md) | ✅ |
| ADR capas | [adr/0003-marketing-os-layered-architecture.md](adr/0003-marketing-os-layered-architecture.md) | ✅ |
| Plan migración | [MARKETING_OS_MIGRATION_PLAN.md](MARKETING_OS_MIGRATION_PLAN.md) | ✅ |
| Recursos API | [MARKETING_OS_API_RESOURCES.md](MARKETING_OS_API_RESOURCES.md) | ✅ |

---

## Sprint 3 — M0 + M1 Corporate Memory ✅

**Spec:** [MARKETING_OS_SPRINT3_MEMORY.md](MARKETING_OS_SPRINT3_MEMORY.md) — cerrado 2026-06-26

| Fase | Entregable | Estado |
|------|------------|--------|
| M0 | `platform_infrastructure/` + `marketing_os.db` | ✅ |
| M1 | `memory_*` + API + bridge MarketingPlan | ✅ |
| M1 | `scripts/migrate_audit_to_memory.py` | ✅ |

---

## Sprint 4 — M2 Company Brain ✅

**Spec:** [MARKETING_OS_SPRINT4_COMPANY_BRAIN.md](MARKETING_OS_SPRINT4_COMPANY_BRAIN.md) — cerrado 2026-06-29

| Fase | Entregable | Estado |
|------|------------|--------|
| M2 | `company_brain_*` + API + facade | ✅ |
| M2 | `company_profiles` schema v2 | ✅ |
| M2 | `migrate_business_context_to_brain.py` | ✅ |

---

## Sprint 5 — M3 Brands ✅

**Spec:** [MARKETING_OS_SPRINT5_BRANDS.md](MARKETING_OS_SPRINT5_BRANDS.md) — cerrado 2026-06-29

| Fase | Entregable | Estado |
|------|------------|--------|
| M3 | `brand_*` + API + facade `marketing_app` | ✅ |
| M3 | `brands` schema v3 | ✅ |
| M3 | `migrate_registry_to_brands.py` | ✅ |

---

## Sprint 6 — M4 Publications (requiere GO)

| Fase | Entregable |
|------|------------|
| M4 | `content_queue.json` → `publications` |

---

## Alineación a Product Vision v2.2

EM+Acción = **Marketing OS**. Núcleo: ciclo **Observar → Analizar → Planificar → Crear → Ejecutar → Medir → Aprender**.

Conceptos transversales: **Empresa Viva** (§5) · **todo observable** · **todo con responsable** · **multiempresa** Tenant→Marcas→Productos.

| Pilar (visión) | Fases del ciclo | En código hoy |
|----------------|-----------------|---------------|
| 1 Company Brain | Observar · Aprender | 🔄 M2 (`company_profiles` + API) |
| 2 Corporate Memory | Observar · Aprender · Medir | 🔄 M1 (`memory_events`) |
| 3 Product Knowledge Base | Observar · Crear · Aprender | Parcial (Knowledge Engine) |
| 4 Brand Center | Crear | 🔄 M3 (`brands` + API) |
| 5 Asset Manager | Crear · Ejecutar | Parcial (`flyers/`, cola) |
| 6 Marketing Brain | Analizar · Planificar | Parcial (planner, propuestas) |
| 7 Roadmap Engine | Planificar | Esbozo (workspace, banner) |
| 8 AI Provider Manager | Crear | En curso (`ai_provider/`) |
| 9 Automation Engine | Ejecutar | Parcial (publicador, órdenes) |
| 10 ROI Engine | Medir · Aprender | ❌ Fragmentado (métricas básicas) |
| Marketing Console | Todas (UI) | Embrión ([WORKSPACE_SHELL.md](WORKSPACE_SHELL.md)) |

**Regla de desarrollo (visión §13):** pilar + fase del ciclo + *¿ayuda a vender más?*

**Plan Maestro (fases A–P):** alineación en iteración posterior.

---

## Prioridad actual (jun 2026)

```
Documentación ✅ · M0 Memory ✅ · M1 Memory ✅ · M2 Brain ✅ · M3 Brands ✅
M4 Publications — próximo (GO)
```

**Regla activa:** código solo con GO explícito por fase M*.

**Principio permanente:** [WORKSPACE_SHELL.md](WORKSPACE_SHELL.md) — un solo shell; embrión de Marketing Console.

**Forma de trabajo:** entregables verificables · Principio 19 · sin docs conceptuales nuevos.

---

## Próximo sprint — Accio AI Provider Manager (acotado)

**Objetivo:** chat y propuestas IA del asistente EM+Acción usando **LiteLLM en CODITO → Ollama local**, sin dependencia de OpenAI.

**Arquitectura acordada:**

```
EM+Acción (ARROZCONPOLLO)
        ↓
Accio AI Provider Manager  ← capa única de salida LLM
        ↓
LiteLLM (CODITO)
        ↓
Ollama / qwen2.5-coder (14B o 7B)
```

**Respaldo futuro (fuera de este sprint):** OCI / Ollama / mistral — solo documentar, no implementar.

### Fuera de alcance (NO GO este sprint)

| Item | Motivo |
|------|--------|
| OpenAI directo (`api.openai.com`) | Decisión producto: IA local primero |
| `OPENAI_API_KEY` en UI / tenant secrets | Reemplazar por config servidor |
| Instalar Ollama/LiteLLM en ARROZCONPOLLO | Usar CODITO existente |
| Manual de operación IA | Después de validar conectividad |
| Nuevos modelos / fine-tuning | Solo usar modelo ya disponible en CODITO |
| Fase M (Community Manager IA) | Depende de este sprint, no es el sprint |

### Estado al corte (2026-06-26)

| Capa | Estado | Notas |
|------|--------|-------|
| `ai_provider/` (config, litellm, manager) | 🔄 Esqueleto | `Motor_Tecnico/accio_engine/ai_provider/` |
| `assistant_llm.py` | 🔄 Parcial | Fachada hacia manager; falta cerrar integración |
| `assistant_service.py` | 🔄 Parcial | Mensajes agnósticos; aún alias `_call_openai` |
| `marketing_planner.py` | 🔄 Parcial | Usa `chat_completion` del manager |
| `/assistant/status` + UI | ❌ Pendiente | Sigue `has_openai_key` / «Sin OpenAI Key» |
| `.env` producción | ❌ Pendiente | Falta `ACCIO_AI_BASE_URL` (CODITO no resolvió desde ARROZCONPOLLO) |
| Script validación CODITO | ❌ Pendiente | `scripts/validate_codito_ai.py` |
| Tests `test_ai_provider.py` | ❌ Pendiente | Actualizar `test_assistant_v1.py` |
| Deprecar `scripts/setup_openai_ia.py` | ❌ Pendiente | Obsoleto con nueva arquitectura |

### Backlog sprint (orden sugerido)

1. **Infra — validar CODITO** (bloqueante)
   - Obtener URL/puerto real de LiteLLM en CODITO
   - Probar desde ARROZCONPOLLO: DNS, firewall, token si aplica
   - Listar modelos disponibles (`GET /v1/models`)
   - Confirmar modelo V1: `qwen2.5-coder:14b` (o el que responda)

2. **Config servidor** (ARROZCONPOLLO `.env`)
   ```env
   ACCIO_AI_PROVIDER=litellm
   ACCIO_AI_BASE_URL=http://<CODITO>:<PUERTO>
   ACCIO_AI_MODEL=qwen2.5-coder:14b
   ACCIO_AI_API_KEY=          # solo si LiteLLM lo exige
   AI_ASSISTANT_ENABLED=true
   ```

3. **Cerrar integración código**
   - Terminar refactor: `assistant_llm` → `ai_provider.manager`
   - `/assistant/status`: `provider`, `provider_reachable`, `llm_available` (quitar `has_openai_key`)
   - UI `plan_slice.js` + `dashboard.html`: estados «IA activa» / «Proveedor no alcanzable» (sin OpenAI)
   - Ocultar o deprecar campo `openai_api_key` en Variables (solo servidor)

4. **Validación funcional**
   - `GET /accio/{tenant}/assistant/status` → `llm_available: true`
   - Chat asistente + propuesta planner con modelo local
   - Reiniciar: `sudo systemctl restart easytech-accio-engine`

5. **Documentación mínima**
   - `docs/ACCIO_AI_PROVIDER_MANAGER.md` (contrato env + arquitectura)
   - Actualizar fila «Asistente» en entregas transversales de este roadmap

### Criterio de cierre sprint

- [ ] ARROZCONPOLLO alcanza LiteLLM en CODITO (ping + al menos 1 modelo)
- [ ] Asistente responde en chat sin OpenAI
- [ ] UI no menciona OpenAI Key al usuario final
- [ ] Tests unitarios del provider pasan
- [ ] Sin regresión Workspace Shell / branding

### Dependencias / riesgos

| Riesgo | Mitigación |
|--------|------------|
| `codito.etsrv.site` no resuelve desde ARROZCONPOLLO | IP privada, `/etc/hosts`, o túnel — definir con ops |
| LiteLLM sin auth vs con token | Probar ambos; documentar en `.env` |
| Modelo 14B lento en primera carga | Fallback a `qwen2.5-coder:7b` documentado |
| Tools (`create_post_drafts`) no soportados por Ollama | Probar; si falla, desactivar tools en V1 y mantener modo reglas |

### Proveedores (inventario infra)

| Servidor | Stack | Modelos | Uso |
|----------|-------|---------|-----|
| **CODITO** | Open WebUI, LiteLLM, Ollama | qwen2.5-coder 14B/7B | **V1 producción EM+Acción** |
| **OCI** | Ollama | mistral | Respaldo / pruebas ligeras (post-V1) |

---

## Vertical Slice 1 — Plan de Marketing (track transversal)

**Objetivo:** Primer flujo end-to-end del **Asistente Ejecutivo de Marketing** atravesando dominio → API → UI — **dentro del Workspace Shell**.

```
Inicio → Plan (Crear/Resumen) → Contexto → Propuestas IA
```

| Capa | Estado | Referencia |
|------|--------|------------|
| Dominio `MarketingPlan` v1.1 | ✅ Congelado | `docs/MARKETING_PLAN_DOMAIN_v1.1.md` |
| Application + JSON adapter | ✅ | `marketing_plan_*` |
| API v1 (`/api/v1/tenants/…/apps/…`) | ✅ 4 endpoints + context + planner | `docs/API_CONTRACT_V1.md` |
| Workspace Shell | 🔄 En curso | `docs/WORKSPACE_SHELL.md` |
| UI módulo `plan_slice` | 🔄 Migrando al shell | `/accio/plan/{tenant}/` |
| Tests integración | ✅ | `tests/test_vertical_slice_1.py` |
| Evidencia visual | ✅ | `Marketing/deliverables/vertical_slice_1/` |

### Revisión UX producto (iterativa)

| # | Pantalla | UX | Deploy |
|---|----------|-----|--------|
| 1 | Inicio (Workspace) | ✅ Aprobación pendiente | — |
| 2 | Crear Plan (wizard) | ✅ Aprobación pendiente | — |
| 3 | Activar Plan | ✅ Aprobación pendiente | — |
| 4 | Context Builder | ✅ Revisada | — |
| 5 | Propuesta IA | ✅ Aprobación pendiente | — |

**Bitácora:** [sessions/2026-06-29-vs1-ux.md](sessions/2026-06-29-vs1-ux.md)

**Congelado hasta post-VS1:** Campaigns, Calendar, Assets, OpenAPI completo, dashboard nuevo integral.

---

## Orden obligatorio V2

```
A → B → C → D → E → F → G → H → I → J → K → L → M → N → O → P
```

VS1 no sustituye fases E–P; valida arquitectura y entrega el primer valor de producto sobre el dominio Plan.

---

## Mapa de fases

| Fase | Nombre | Estado | Prioridad |
|------|--------|--------|-----------|
| **A** | Base técnica | 🔄 ~90% | Cerrar backup + entornos |
| **B** | Multi-Tenant Core | ✅ ~95% | Apps por tenant + login plataforma |
| **C** | Configuration Center | ✅ ~98% | Guía anti-JSON-manual |
| **D** | Knowledge Engine | 🔄 ~50% | Matriz producto-sector |
| **E** | Opportunity Engine | 📋 | Alta (post-D) |
| **F** | Campaign Engine | 📋 | Alta |
| **G** | Image Engine | 📋 | Media |
| **H** | Publisher | 🔄 LI+FB parcial | Media |
| **I** | Landing Manager | 🔄 producto + Relatic | Alta |
| **J** | CRM Integration | 🔄 Odoo + leads locales | Alta |
| **K** | Analytics | 🔄 básico | Media |
| **L** | Learning Engine | 📋 | Media |
| **M** | Community Manager IA | 📋 | Baja |
| **N** | Scheduler | 🔄 calendario manual | Media |
| **O** | Automation Engine | 📋 | Media |
| **P** | API Marketplace | 🔄 API v1 Plan (no marketplace) | Baja |

---

## Fase A — Base técnica

**Objetivo:** DEV · TEST · PROD independientes. Motor estable.

| Tarea | Estado |
|-------|--------|
| systemd + servicios OAuth | ✅ |
| Git + repo documentado | ✅ |
| nginx + proxy `/accio/` | ✅ |
| emaccion.etsrv.site vhost | 🔄 |
| SSL origen / Cloudflare Full | 🔄 |
| Backup `.env` cifrado | 🔄 `scripts/backup_secrets.sh` |
| Separar DEV / TEST / PROD | 🔄 `env_loader` + units dev/test |
| Logs y deploy documentados | 🔄 `docs/INVENTARIO_DESPLIEGUE.md` |
| Bitácora sesiones | ✅ `docs/sessions/` |

**Cierre:** checklist en `docs/fases/A_CHECKLIST.md` (pendiente) + evidencia pruebas.

---

## Fase B — Multi-Tenant Core

**Objetivo:** Un motor, N clientes, cero datos mezclados.

| Tarea | Estado |
|-------|--------|
| `registry.json` + tenants easytech/relatic | ✅ |
| API `/accio/{tenant_id}/` | ✅ |
| Dashboard por tenant | ✅ |
| Login plataforma + selector empresa | ✅ |
| Datos aislados por carpeta | ✅ |
| Modelo tenant (subdomain, registration, branding) | ✅ |
| Usuarios por tenant (`auth.db`) | ✅ |
| **Apps por tenant** (`apps/{app_id}/`) | ✅ cola, KB, campañas por app |
| CRUD empresas plataforma (`super_admin`) | ✅ |
| `tenant_id` + `app_id` en modelo editorial | 🔄 |
| Tests aislamiento | ✅ |
| Deprecar `Marketing/accio/` legacy | ❌ |

**Doc:** [EMACCION_TENANT_VS_APP.md](EMACCION_TENANT_VS_APP.md) · [EMACCION_PHASE_M_MULTI_TENANT.md](EMACCION_PHASE_M_MULTI_TENANT.md)

---

## Fase C — Configuration Center

**Objetivo:** Toda configuración desde UI. Sin JSON manual.

| Tarea | Estado |
|-------|--------|
| Tab Configuración (13 sub-secciones) | ✅ |
| Secretos cifrados SQLite | ✅ |
| CRUD usuarios, roles, productos, landings, variables | ✅ |
| CRUD empresas plataforma | ✅ |
| Probar conexión conectores | ✅ |
| RBAC en API | ✅ |
| Logs y backup desde UI | ✅ |
| Guía operativa anti-JSON-manual | ❌ |

**Doc:** [EMACCION_PHASE_N_TENANT_SETTINGS.md](EMACCION_PHASE_N_TENANT_SETTINGS.md)

---

## Fase D — Knowledge Engine

**Objetivo:** Conocimiento completo del portafolio por tenant/app.

| Tarea | Estado |
|-------|--------|
| KB por tenant y por app | ✅ |
| `business_context.json` + editorial_rules | ✅ |
| API + tab Conocimiento + CRUD artículos | ✅ |
| Context Builder V1 (VS1) | ✅ integrado en slice |
| Matriz producto-sector-necesidad | ❌ |
| Converso + competencia en KB | ❌ |
| Q&A automático | ❌ |

**Doc:** [EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md](EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md)

---

## Entregas transversales recientes (no son fases V2)

| Entrega | Estado | Notas |
|---------|--------|-------|
| Landing producto `/accio/producto/` | ✅ | SaaS enterprise v2 |
| Asistente EM+Acción V1 (chat + órdenes) | 🔄 | Panel dashboard; **IA pendiente Provider Manager → CODITO** |
| Accio AI Provider Manager | 📋 | Próximo sprint — § arriba |
| Vista Publicaciones + estados editoriales | ✅ | `editorial.py` |
| Leads locales + métricas por app | ✅ | |
| Tenant Relatic (catálogo, legal, landings) | ✅ | |
| API pública v1 — recurso `MarketingPlan` | ✅ | Primer recurso; no marketplace |

---

## Fases E–P — Resumen

| Fase | Criterio de cierre (resumen) |
|------|------------------------------|
| **E** | Señal web → `opportunities.json` clasificado |
| **F** | Oportunidad → campaña draft con copy, CTA, landing |
| **G** | Imágenes generadas por formato/canal |
| **H** | LI+FB+IG publicando con post ID registrado |
| **I** | 5+ landings producto con UTM |
| **J** | Lead → EN1 + adaptadores Odoo/HubSpot/Zoho |
| **K** | Dashboard conversión por campaña/producto |
| **L** | Feedback loop campaña → estrategia |
| **M** | Respuesta IA comentarios/DMs |
| **N** | Scheduler sugiere hora/día óptimo |
| **O** | Nurturing email/WhatsApp |
| **P** | API pública documentada + auth marketplace |

Detalle completo: [EMACCION_V2_PLAN_MAESTRO.md](EMACCION_V2_PLAN_MAESTRO.md) §7–19.

---

## Dashboard objetivo (§20 plan V2)

```
Dashboard · Oportunidades · Campañas · Publicaciones · Leads · CRM
Productos · Knowledge · Conectores · Automatizaciones · Métricas · Configuración
```

**Hoy:** dashboard operativo legacy + módulo **Plan** (`/accio/plan/{tenant}/`) como primer paso hacia el dashboard objetivo.

---

## Editorial (contenido publicado)

Regla interina **3 valor + 1 venta** (75/25). Objetivo Fase E matriz: **95/5**.  
Calendario: `Marketing/CALENDARIO_PUBLICACION.md`

---

## Criterio final V2 (§27)

12 capacidades end-to-end: detectar → clasificar → producto → campaña → contenido → publicar → landing → lead → CRM → seguimiento → medir → aprender.

**Hito intermedio VS1:** plan estratégico → contexto → propuesta IA (sin ejecución automática de campañas).

---

## Referencias

| Doc | Contenido |
|-----|-----------|
| [MARKETING_OS_CONSTITUTION.md](MARKETING_OS_CONSTITUTION.md) | Reglas inmutables |
| [MARKETING_OS_ARCHITECTURE.md](MARKETING_OS_ARCHITECTURE.md) | Capas e implementación |
| [MARKETING_OS_MIGRATION_PLAN.md](MARKETING_OS_MIGRATION_PLAN.md) | Migración M0–M11 |
| [MARKETING_OS_API_RESOURCES.md](MARKETING_OS_API_RESOURCES.md) | Recursos `/api/v1` |
| [VERTICAL_SLICE_1.md](VERTICAL_SLICE_1.md) | Slice técnico |
| [MARKETING_PLAN_DOMAIN_v1.1.md](MARKETING_PLAN_DOMAIN_v1.1.md) | Dominio congelado (Principio 5 — IA agnóstica) |
| [API_CONTRACT_V1.md](API_CONTRACT_V1.md) | Contrato API pública |
| [WORKSPACE_SHELL.md](WORKSPACE_SHELL.md) | Shell único de navegación |
| [EMACCION_V2_PLAN_MAESTRO.md](EMACCION_V2_PLAN_MAESTRO.md) | Plan estratégico completo |
| [EMACCION_V2_ESTADO.md](EMACCION_V2_ESTADO.md) | Estado código vs plan |
| [CONTEXTO.md](CONTEXTO.md) | Operación diaria |
| [sessions/2026-06-29-vs1-ux.md](sessions/2026-06-29-vs1-ux.md) | Bitácora VS1 UX |
| [ACCIO_AI_PROVIDER_MANAGER.md](ACCIO_AI_PROVIDER_MANAGER.md) | Contrato env + LiteLLM CODITO |
