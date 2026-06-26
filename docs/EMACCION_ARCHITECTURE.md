# EM+Acción — Arquitectura objetivo

**Versión:** 1.0 · **Fecha:** 2026-06-22  
**Estado:** Documento de diseño — no todo implementado

---

## 1. Principio rector

EMAcción es el **único motor comercial** del ecosistema EasyTech. Los productos son destinos, no competidores de marketing.

```
EN1 · EPOSOne · EPayRoll · Odoo · EClassOne · Converso
                    ▲
                    │ routing por necesidad
                    │
                 EMAcción
```

---

## 2. Diagrama de flujo comercial

```
Internet / Redes / Fuentes públicas
        │
        ▼
┌───────────────────────────────────────┐
│           EMAcción (Cerebro)          │
│                                       │
│  ┌─────────────┐  ┌────────────────┐  │
│  │ Knowledge   │  │ Opportunity    │  │
│  │ Engine      │◄─┤ Engine         │  │
│  └──────┬──────┘  └───────┬────────┘  │
│         │                 │           │
│         ▼                 ▼           │
│  ┌─────────────────────────────────┐  │
│  │      Campaign Engine IA       │  │
│  └──────────────┬──────────────────┘  │
│                 │                     │
│  ┌──────────────▼──────────────────┐  │
│  │         Publisher               │  │
│  │  LI · FB · IG · Blog · Email    │  │
│  └──────────────┬──────────────────┘  │
│                 │                     │
│  ┌──────────────▼──────────────────┐  │
│  │      Analytics Engine           │  │
│  └─────────────────────────────────┘  │
└───────────────────────────────────────┘
        │
        ▼
Landing específica (por producto)
        │
        ▼
Formulario + UTM
        │
        ▼
EN1 CRM
        │
        ▼
Seguimiento (email · WhatsApp · tarea vendedor · demo)
        │
        ▼
Cliente
        │
        ▼
Optimización (feedback a EMAcción)
```

---

## 3. Capas del sistema

### 3.1 Knowledge Engine (Fase E)

**Qué sabe:** productos, sectores, problemas, diferenciadores, CTAs, objeciones, FAQs, casos de éxito.

**Fuentes:** `Marketing/knowledge/` · `business_context.json` · `editorial_rules.json`

**Responde:**
- ¿Qué vende EasyTech?
- ¿A quién?
- ¿Qué problema resuelve cada producto?
- ¿Qué CTA y landing usar?

### 3.2 Opportunity Engine (Fase F)

**Entrada:** publicaciones, señales web, scraper, keywords.

**Proceso:**
1. Detectar señal
2. Clasificar sector (educación, retail, RRHH, ERP…)
3. Identificar necesidad
4. Recomendar producto
5. Asignar prioridad y canal

**Salida:** `opportunities.json` con estado `detected` → `classified` → `approved`

**Ejemplo:**

| Señal | Sector | Producto | Landing |
|-------|--------|----------|---------|
| Universidad anuncia congreso | Educación | EN1 | `/en1-eventos` |
| Restaurante busca POS | Retail | EPOSOne | `/eposone` |
| Consulta planilla quincena | RRHH | EPayRoll | `/epayroll` |

### 3.3 Campaign Engine (Fase G)

**Entrada:** oportunidad aprobada + knowledge.

**Genera:** copy · título · hashtags · CTA · landing · prompt imagen · canal · fecha.

**Salida:** campaña en `draft` → `approved` → cola editorial.

### 3.4 Publisher (Fase H)

**Canales por prioridad:**

| Fase | Canales |
|------|---------|
| 1 | LinkedIn, Facebook, Instagram |
| 2 | Blog EasyTech, Email, Google Business |
| 3 | X, YouTube, TikTok, Ads |

**Registra:** ID externo, timestamp, errores, UTM.

### 3.5 EN1 CRM Sync (Fase I)

**Módulo:** `en1_sync.py`

**Campos lead:**
- origen: `EMAccion`
- canal, campaña, producto, landing, UTM
- estado, responsable, notas

**Odoo:** transitorio hasta EN1 estable.

### 3.6 Analytics Engine (Fase J)

**Métricas:** clics · CTR · leads · demos · ventas · CPL · rendimiento producto/campaña.

**UTM estándar:** `utm_source` · `utm_medium` · `utm_campaign` · `utm_content` · `utm_product`

---

## 4. Agentes especializados (Fase K)

```
EMAcción
├── Trend Hunter          → busca oportunidades
├── Opportunity Analyzer  → clasifica necesidades
├── Campaign Planner      → decide campaña
├── Copywriter IA         → escribe posts
├── Image Creator         → genera imágenes
├── Publisher             → publica
├── Community Manager IA  → responde comentarios
├── Lead Analyzer         → califica prospectos
└── Sales Assistant       → agenda demos
```

---

## 5. Arquitectura técnica actual (implementada)

```
Navegador → nginx (n8n.etsrv.site)
              │
              ▼
         accio_engine :8092
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
LinkedIn   Meta OAuth  Google/TikTok OAuth
:8091      :8093        :8094/:8095
    │         │
publishers  meta_publisher.py
    │
content_queue.json · flyers/ · Odoo CRM
```

---

## 6. Matriz producto-sector

| Sector | Señales | Producto | CTA |
|--------|---------|----------|-----|
| Educación superior | congresos, cursos, tesis | EN1 / EClassOne | DEMO |
| Retail | POS, inventario, tienda | EPOSOne | DIAGNÓSTICO |
| RRHH | planilla, nómina, CSS | EPayRoll | PLANILLA |
| PYME general | ERP, FE, integración | Odoo + FE | DIAGNÓSTICO |
| Servicios | CRM, todo-en-uno | EN1 | EN1 / DEMO |
| EdTech K-12 | matrícula, notas | EClassOne | DEMO |

---

## 7. Flujo diario objetivo (08:00)

```
08:00 Trend Hunter escanea fuentes
  → universidades, empresas, restaurantes, contadores, hospitales
  → clasifica cada señal
  → Opportunity Analyzer asigna producto
  → Campaign Planner genera campaña draft
  → operador aprueba (o auto si confianza alta)
  → Publisher publica
  → Analytics mide clics y leads
  → feedback mejora próxima campaña
```

---

## 8. Referencias

- Estado actual: `CONTEXTO.md`
- Brecha: `EMACCION_GAP_ANALYSIS.md`
- Roadmap: `ROADMAP.md`
- Fase E: `EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md`
