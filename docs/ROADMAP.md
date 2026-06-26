# EM+Acción — Roadmap estratégico EasyTech

**Producto estratégico:** EMAcción es el **motor comercial central** del ecosistema EasyTech.  
**Regla:** No es un publicador de contenido — es motor de oportunidades, campañas, publicación, captura y medición.  
**Repo:** `github.com/shidalgo0925/easytech_marketing` · **VPS:** `/opt/easytech_marketing`

**Visión:**

```
Internet → EMAcción → Oportunidad → Producto → Campaña → Publicación
    → Landing → EN1 CRM → Seguimiento → Demo → Analítica → Optimización
```

**Orden de implementación:**

1. Consolidar base técnica (Fase A)
2. Completar Knowledge Engine (Fase E)
3. Opportunity Engine (Fase F)
4. Campaign Engine (Fase G)
5. Publisher multicanal (Fase H)
6. EN1 CRM (Fase I)
7. Analítica (Fase J)
8. Agentes especializados (Fase K)

> **No implementar runtime sin GO explícito.** Este documento es la fuente de verdad del roadmap.

---

## Mapa de fases

| Fase | Nombre | Estado | Prioridad |
|------|--------|--------|-----------|
| **A** | Base técnica EMAcción | 🔄 70% | Alta |
| **B** | Canales actuales | 🔄 Parcial | Alta |
| **C** | Cola editorial | 🔄 Parcial | Media |
| **D** | Landings comerciales | 📋 Pendiente | Alta |
| **E** | Knowledge Engine | ⏳ **Inmediata** | **Crítica** |
| **F** | Opportunity Engine | 📋 Pendiente | Alta |
| **G** | Campaign Engine IA | 📋 Pendiente | Alta |
| **H** | Publisher multicanal | 🔄 Parcial | Media |
| **I** | EN1 CRM Integration | 📋 Pendiente | Alta |
| **J** | Analytics Engine | 📋 Pendiente | Media |
| **K** | Agentes especializados | 📋 Futuro | Baja |

Docs relacionados: `EMACCION_ARCHITECTURE.md` · `EMACCION_GAP_ANALYSIS.md` · `EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md`

---

## Fase A — Base técnica EMAcción

**Objetivo:** Plataforma estable, documentada y desplegable.

| Tarea | Estado |
|-------|--------|
| Servicio systemd `easytech-accio-engine` :8092 | ✅ |
| Dashboard protegido `ACCIO_API_KEY` | ✅ |
| Git en GitHub | ✅ |
| `docs/INSTALACION.md` | ✅ |
| Backup `.env` offline cifrado | ❌ |
| Separar DEV / TEST / PROD | ❌ |
| Limpiar archivos huérfanos en repo | 🔄 |
| Documentar deploy completo | 🔄 |

**Criterio de cierre:** Repo limpio, deploy documentado, `.env` respaldado, servicio estable.

---

## Fase B — Canales actuales

**Objetivo:** LinkedIn, Facebook e Instagram publicando correctamente.

| Canal | Estado |
|-------|--------|
| LinkedIn | ✅ 3 posts publicados, cron activo |
| Facebook | ✅ OAuth OK, publisher listo, sin publicar aún |
| Instagram | ⏳ Publisher sí, falta `META_IG_USER_ID` |
| Google Business | ⏳ Código sí, falta OAuth |
| YouTube / TikTok / Ads | ❌ Stub |
| X / Blog / Email | ❌ No existe |

**Criterio de cierre:** LI + FB + IG publicando en producción.

---

## Fase C — Cola editorial

**Objetivo:** Planificar, aprobar, publicar y registrar resultado.

Archivos: `content_queue.json` · `campaigns.json` · `calendar.json` · `orders.json` · `tasks.json`

| Tarea | Estado |
|-------|--------|
| Cola 22 posts, 3 publicados | ✅ |
| Regla 3 valor + 1 venta (75/25 interina) | ✅ |
| Estados draft/approved/scheduled/published/failed | ❌ |
| Modelo de campaña unificado | 🔄 |

**Criterio de cierre:** Cola con estados completos y trazabilidad post-publicación.

---

## Fase D — Landings comerciales

**Objetivo:** Una landing por producto con formulario, UTM y origen EMAcción.

| Landing | Producto | Estado |
|---------|----------|--------|
| `/guia/` | FE Panamá (genérica) | ✅ |
| `/en1-eventos` | EN1 eventos | ❌ |
| `/en1-cursos` | EN1 cursos | ❌ |
| `/eposone` | EPOSOne | ❌ |
| `/epayroll` | EPayRoll | ❌ |
| `/odoo` | Odoo + FE | ❌ |
| `/eclassone` | EClassOne | ❌ |

Cada landing: mensaje · CTA · formulario · UTM · producto · conexión futura EN1 CRM.

**Criterio de cierre:** 6 landings mínimas operativas.

---

## Fase E — Knowledge Engine ⏳ PRIORITARIA

**Objetivo:** EMAcción conoce todo el portafolio EasyTech.

Ver **`docs/EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md`**.

| Tarea | Estado |
|-------|--------|
| `Marketing/knowledge/` (fichas MD) | 🔄 Iniciado |
| `Marketing/accio/business_context.json` | 🔄 Iniciado |
| `Marketing/accio/editorial_rules.json` | 🔄 Iniciado |
| `knowledge_api.py` (módulo preparatorio) | 🔄 Sin integrar a `app.py` |
| Endpoints API knowledge en motor | ❌ |
| UI Configuración en dashboard | ❌ |
| Matriz producto-sector-necesidad | ❌ |

**Criterio de cierre:** Motor consulta KB y genera contenido coherente por producto y sector.

---

## Fase F — Opportunity Engine

**Objetivo:** Señal externa → oportunidad comercial clasificada.

| Tarea | Estado |
|-------|--------|
| `opportunity_engine.py` | ❌ |
| `Marketing/accio/opportunities.json` | ❌ |
| Detección por keywords | ❌ |
| Clasificación sector/necesidad/producto | ❌ |
| Estados: detected → classified → approved → campaign_created | ❌ |

**Criterio de cierre:** Una publicación detectada se convierte en oportunidad con producto recomendado.

---

## Fase G — Campaign Engine IA

**Objetivo:** Oportunidad aprobada → campaña lista para revisión.

Genera: copy · hashtags · CTA · landing · prompt imagen · canal · fecha.

**Criterio de cierre:** Oportunidad aprobada produce campaña en estado `draft`.

---

## Fase H — Publisher multicanal

**Objetivo:** Post aprobado publicable en LI + FB + IG.

| Prioridad | Canales |
|-----------|---------|
| Fase inicial | LinkedIn, Facebook, Instagram |
| Segunda | Blog, Email, Google Business |
| Tercera | X, YouTube, TikTok, Ads |

**Criterio de cierre:** Un post aprobado publica en los 3 canales principales con ID externo registrado.

---

## Fase I — EN1 CRM Integration

**Objetivo:** Todo lead de EMAcción entra en EN1 CRM (Odoo queda transitorio).

| Tarea | Estado |
|-------|--------|
| `en1_sync.py` | ❌ |
| Lead con origen, canal, campaña, producto, UTM, landing | ❌ |
| Odoo como transición | ✅ Actual |

**Criterio de cierre:** Formulario landing → EN1 CRM automático.

---

## Fase J — Analytics Engine

**Objetivo:** Saber qué campañas generan leads reales.

Métricas: clics · CTR · leads · demos · ventas · costo/lead · rendimiento por producto/campaña.

UTM: `utm_source` · `utm_medium` · `utm_campaign` · `utm_content` · `utm_product`

**Criterio de cierre:** Dashboard de conversión por campaña y producto.

---

## Fase K — Agentes especializados (futuro)

| Agente | Rol |
|--------|-----|
| Trend Hunter | Busca oportunidades |
| Opportunity Analyzer | Clasifica necesidades |
| Campaign Planner | Decide campaña |
| Copywriter IA | Escribe publicaciones |
| Image Creator | Genera imágenes |
| Publisher | Publica |
| Community Manager IA | Responde comentarios |
| Lead Analyzer | Califica prospectos |
| Sales Assistant | Agenda demos |

**Criterio de cierre:** EMAcción opera como agente comercial asistido.

---

## Reglas editoriales

| Versión | Regla | Dónde |
|---------|-------|-------|
| Interina (C) | 3 valor + 1 venta (75/25) | `content_queue.json` |
| Objetivo (E) | Matriz 95/5 por tipo | `editorial_rules.json` |

---

## Referencias

| Doc | Contenido |
|-----|-----------|
| [CONTEXTO.md](CONTEXTO.md) | Estado operativo |
| [EMACCION_ARCHITECTURE.md](EMACCION_ARCHITECTURE.md) | Arquitectura objetivo |
| [EMACCION_GAP_ANALYSIS.md](EMACCION_GAP_ANALYSIS.md) | Brecha hoy vs V1 |
| [EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md](EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md) | Fase E detalle |
| [ACCIO_MARKETING_ENGINE.md](ACCIO_MARKETING_ENGINE.md) | Plan maestro histórico |
| [CONECTAR_REDES.md](CONECTAR_REDES.md) | OAuth por canal |

**Actualizado:** 2026-06-22 · **Último commit base:** `6732a05`
