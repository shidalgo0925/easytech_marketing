# EM+Acción V2 — Estado actual vs Plan Maestro

**Fecha:** 2026-06-26  
**Referencia:** [EMACCION_V2_PLAN_MAESTRO.md](EMACCION_V2_PLAN_MAESTRO.md)

Este documento mapea **qué existe hoy en código** frente al Plan V2.  
**No confundir con cierre de fase** — una fase solo se cierra con checklist + pruebas + GO.

---

## Resumen ejecutivo

| Fase V2 | Nombre | Estado real | % estimado |
|---------|--------|-------------|------------|
| **A** | Base técnica | 🔄 ~90% | Cerrar backup + .env.prod en deploy/secrets |
| **B** | Multi-Tenant Core | ✅ ~95% | Login plataforma + selector empresa + auth.db |
| **C** | Configuration Center | ✅ ~98% | CRUD completo + usuarios en auth.db |
| **D** | Knowledge Engine | 🔄 ~50% | KB integrada + CRUD artículos; falta matriz |
| **E–P** | Resto del plan | 📋 Pendiente | 0–10% |

**Fase activa recomendada:** **D** Knowledge completo → **E** Opportunity.

---

## Fase A — Base técnica

| Ítem | Estado | Notas |
|------|--------|-------|
| Repo GitHub | ✅ | `easytech_marketing` |
| systemd `easytech-accio-engine` | ✅ | :8092 |
| OAuth services (LI, Meta, Google, TikTok) | ✅ | :8091–8095 |
| nginx `n8n.etsrv.site` | ✅ | `/accio/` proxy |
| nginx `emaccion.etsrv.site` | 🔄 | HTTP origen; SSL Cloudflare |
| Documentación | 🔄 | V2 + fases parciales |
| Backup `.env` cifrado | 🔄 | `scripts/backup_secrets.sh` |
| DEV / TEST / PROD separados | 🔄 | `env_loader` + systemd dev/test |
| Logs centralizados | 🔄 | `logs/` local |
| Git limpio | 🔄 | |

**Bloqueantes para cerrar A:** entornos DEV/TEST/PROD · backup `.env` · SSL origen emaccion (opcional con CF Full).

---

## Fase B — Multi-Tenant Core

| Ítem | Estado | Notas |
|------|--------|-------|
| `Marketing/tenants/registry.json` | ✅ | easytech + relatic |
| Carpetas `tenants/{id}/` | ✅ | |
| API `/accio/{tenant_id}/...` | ✅ | |
| Dashboard `/accio/dashboard/{tenant_id}/` | ✅ | |
| Aislamiento cola/KB/campañas | ✅ | Verificado easytech vs relatic |
| Modelo tenant (logo, color, dominio) | ✅ | `tenant.json` + branding en Configuración |
| `tenant_id` en todas las tablas | 🔄 | JSON por carpeta; SQLite secrets + auth |
| Usuarios por empresa | ✅ | `auth.db` + `user_tenants` + CRUD UI |
| Login plataforma + selector empresa | ✅ | `/accio/login/` → `/accio/empresas/` |
| CRUD empresas (super_admin) | ✅ | crear · editar · suspender · reactivar |
| Branding por tenant | ✅ | CSS + formulario Información general |
| Tests aislamiento automatizados | ✅ | 6 tests + auth/knowledge CRUD |

**Bloqueantes para cerrar B:** deprecar paths legacy `Marketing/accio/` donde aún se lean datos globales.

---

## Fase C — Configuration Center

| Ítem | Estado | Notas |
|------|--------|-------|
| Tab Configuración (13 sub-secciones) | ✅ | Dashboard |
| `settings_center.py` + `/settings/center` | ✅ | Vista unificada |
| CRUD usuarios → auth.db | ✅ | `sync_tenant_users` |
| CRUD productos / variables / landings | ✅ | Tabla + eliminar fila |
| CRUD roles personalizados | ✅ | `users.json` definiciones |
| CRUD empresas plataforma | ✅ | `tenant_provisioning.py` |
| Usuarios (login real) | ✅ | Sesión Flask + auth.db |
| Logs y backup desde UI | ✅ | |
| Almacén cifrado `tenant_secrets.db` | ✅ | Fernet |
| Probar conexión | ✅ | LI, Meta, Odoo parcial |
| RBAC enforced en API | ✅ | `rbac.py` |
| Upload logo | ✅ | `POST /settings/logo` |
| Auditoría | 🔄 | `settings_audit.log` en UI |

**Cerrada en código.** Pendiente: guía operativa anti-JSON-manual.

---

## Fase D — Knowledge Engine

| Ítem | Estado | Notas |
|------|--------|-------|
| `tenants/{id}/knowledge/` | ✅ | easytech |
| `business_context.json` por tenant | ✅ | |
| `editorial_rules.json` | ✅ | |
| API knowledge + generate-topic | ✅ | |
| Tab Conocimiento dashboard | ✅ | |
| CRUD artículos KB (UI) | ✅ | POST/DELETE `/knowledge` |
| Matriz producto-sector-necesidad | ❌ | |
| Converso en KB | ❌ | |
| Q&A automático | ❌ | |

---

## Fases E–P — Pendientes

| Fase | Estado | Existe hoy |
|------|--------|------------|
| E Opportunity | ❌ | — |
| F Campaign | ❌ | generador temas básico (no oportunidad→campaña) |
| G Image | 🔄 | flyers estáticos, sin IA generativa |
| H Publisher | 🔄 | LI ✅ · FB listo · IG parcial |
| I Landing Manager | 🔄 | solo `/guia/` |
| J CRM | 🔄 | Odoo; EN1/HubSpot/Zoho ❌ |
| K Analytics | 🔄 | métricas básicas Odoo |
| L Learning | ❌ | — |
| M Community IA | ❌ | — |
| N Scheduler | 🔄 | calendario manual |
| O Automation | ❌ | — |
| P API Marketplace | 🔄 | API REST interna, no marketplace |

---

## Dashboard actual vs definitivo (§20)

| Tab plan V2 | Tab hoy | Estado |
|-------------|---------|--------|
| Dashboard | Resumen | ✅ |
| Oportunidades | — | ❌ |
| Campañas | Campañas | ✅ |
| Publicaciones | (en Resumen/cola) | 🔄 |
| Leads | (en Resumen/Odoo) | 🔄 |
| CRM | — | ❌ |
| Productos | — | ❌ |
| Knowledge | Conocimiento | ✅ |
| Conectores | Conectores | ✅ |
| Automatizaciones | — | ❌ |
| Métricas | Métricas | ✅ |
| Configuración | Configuración | ✅ CRUD completo |

---

## Próximos pasos (orden V2)

1. **Completar Fase D** — matriz editorial, Converso en KB
2. **Fase E** — Opportunity Engine
3. **Cron multi-empresa** — publicadores recorren todas las empresas activas
4. **Wizard onboarding** — crear empresa en 7 pasos
5. **EN1 sync** — leads a CRM EN1
6. Cerrar **Fase A** — DEV/TEST/PROD + backup `.env`

> **Sin GO explícito no se avanza runtime más allá de la fase activa.**

---

## Evidencia reciente (PROD)

- Dashboard: https://emaccion.etsrv.site/accio/dashboard/easytech/
- Login: https://emaccion.etsrv.site/accio/login/
- Tenants: `easytech` (8+ posts LI pendientes) · `relatic` (vacío, aislado)
- Auth: `Marketing/tenants/.secrets/auth.db`
- Tests: 25 unit tests OK (jun 2026)
- Fix crítico: `switchTenant` duplicado en `dashboard.html` rompía carga de datos

**Actualizado:** 2026-06-26 · **Contexto sesión:** [EMACCION_CONTEXTO_OPERATIVO.md](EMACCION_CONTEXTO_OPERATIVO.md)
