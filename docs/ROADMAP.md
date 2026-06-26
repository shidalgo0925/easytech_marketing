# EM+Acción V2 — Roadmap operativo

**Producto:** EM+Acción (EasyMarketingOne)  
**Plan maestro:** [EMACCION_V2_PLAN_MAESTRO.md](EMACCION_V2_PLAN_MAESTRO.md)  
**Estado vs código:** [EMACCION_V2_ESTADO.md](EMACCION_V2_ESTADO.md)  
**Regla:** **No implementar una fase hasta cerrar completamente la anterior.**  
**Runtime:** requiere **GO explícito** por fase.

---

## Orden obligatorio V2

```
A → B → C → D → E → F → G → H → I → J → K → L → M → N → O → P
```

---

## Mapa de fases

| Fase | Nombre | Estado | Prioridad |
|------|--------|--------|-----------|
| **A** | Base técnica | 🔄 ~75% | **Activa — cerrar** |
| **B** | Multi-Tenant Core | 🔄 ~65% | **Activa — cerrar** |
| **C** | Configuration Center | 🔄 ~25% | Alta |
| **D** | Knowledge Engine | 🔄 ~35% | Alta |
| **E** | Opportunity Engine | 📋 | Alta |
| **F** | Campaign Engine | 📋 | Alta |
| **G** | Image Engine | 📋 | Media |
| **H** | Publisher | 🔄 parcial | Media |
| **I** | Landing Manager | 📋 | Alta |
| **J** | CRM Integration | 🔄 Odoo | Alta |
| **K** | Analytics | 🔄 básico | Media |
| **L** | Learning Engine | 📋 | Media |
| **M** | Community Manager IA | 📋 | Baja |
| **N** | Scheduler | 🔄 manual | Media |
| **O** | Automation Engine | 📋 | Media |
| **P** | API Marketplace | 📋 | Baja |

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
| Backup `.env` cifrado | ❌ |
| Separar DEV / TEST / PROD | ❌ |
| Logs y deploy documentados | 🔄 |

**Cierre:** checklist en `docs/fases/A_CHECKLIST.md` (pendiente) + evidencia pruebas.

---

## Fase B — Multi-Tenant Core

**Objetivo:** Un motor, N clientes, cero datos mezclados.

| Tarea | Estado |
|-------|--------|
| `registry.json` + tenants easytech/relatic | ✅ |
| API `/accio/{tenant_id}/` | ✅ |
| Dashboard por tenant | ✅ |
| Datos aislados por carpeta | ✅ |
| Modelo tenant (logo, color, dominio) | ❌ |
| Usuarios por tenant | ❌ |
| Branding por tenant | ❌ |
| `tenant_id` en todo el modelo | 🔄 |
| Tests aislamiento | ❌ |
| Deprecar `Marketing/accio/` legacy | ❌ |

**Doc detalle:** [EMACCION_PHASE_M_MULTI_TENANT.md](EMACCION_PHASE_M_MULTI_TENANT.md) (≡ Fase B V2)

---

## Fase C — Configuration Center

**Objetivo:** Toda configuración desde UI. Sin JSON manual.

| Tarea | Estado |
|-------|--------|
| Tab Configuración (conectores, CRM, API key) | ✅ |
| Secretos cifrados SQLite | ✅ |
| Probar conexión | ✅ |
| Menú completo (usuarios, roles, productos, IA…) | ❌ |
| Variables · logs · backups desde UI | ❌ |
| RBAC | ❌ |

**Doc detalle:** [EMACCION_PHASE_N_TENANT_SETTINGS.md](EMACCION_PHASE_N_TENANT_SETTINGS.md) (≡ parte de Fase C V2)

---

## Fase D — Knowledge Engine

**Objetivo:** Conocimiento completo del portafolio por tenant.

| Tarea | Estado |
|-------|--------|
| KB por tenant (`knowledge/`) | ✅ easytech |
| business_context + editorial_rules | ✅ |
| API + tab Conocimiento | ✅ |
| Matriz producto-sector-necesidad | ❌ |
| Converso + competencia | ❌ |
| Q&A automático | ❌ |

**Doc:** [EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md](EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md)

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
| **P** | API pública documentada + auth |

Detalle completo: [EMACCION_V2_PLAN_MAESTRO.md](EMACCION_V2_PLAN_MAESTRO.md) §7–19.

---

## Dashboard objetivo (§20 plan V2)

```
Dashboard · Oportunidades · Campañas · Publicaciones · Leads · CRM
Productos · Knowledge · Conectores · Automatizaciones · Métricas · Configuración
```

---

## Criterio final V2 (§27)

12 capacidades end-to-end: detectar → clasificar → producto → campaña → contenido → publicar → landing → lead → CRM → seguimiento → medir → aprender.

---

## Referencias

| Doc | Contenido |
|-----|-----------|
| [EMACCION_V2_PLAN_MAESTRO.md](EMACCION_V2_PLAN_MAESTRO.md) | Plan estratégico completo |
| [EMACCION_V2_ESTADO.md](EMACCION_V2_ESTADO.md) | Estado código vs plan |
| [CONTEXTO.md](CONTEXTO.md) | Operación diaria |
| [EMACCION_ARCHITECTURE.md](EMACCION_ARCHITECTURE.md) | Arquitectura |
| [EMACCION_GAP_ANALYSIS.md](EMACCION_GAP_ANALYSIS.md) | Brecha histórica |

**Actualizado:** 2026-06-26 · **Versión roadmap:** 2.0
