# EM+Acción — Fase E: Knowledge Engine

**Prioridad:** Inmediata · **Estado:** Iniciado (~25%) · **Bloquea:** Opportunity Engine, Campaign Engine, contenido IA coherente

---

## 1. Qué es

El **Knowledge Engine** es la memoria estructurada de EMAcción. Sin él, la IA publica ruido. Con él, cada campaña conoce productos, sectores, problemas y CTAs de EasyTech.

Es la **base de todos los agentes futuros** (Fases F–K).

---

## 2. Qué debe conocer

### Productos

| Producto | Archivo | Estado |
|----------|---------|--------|
| EasyTech Services | `knowledge/easytech.md` | ✅ |
| Odoo + FE | `knowledge/odoo_fe.md` | ✅ |
| EN1 | `knowledge/en1.md` | ✅ |
| EPOSOne | `knowledge/eposone.md` | ✅ |
| EClassOne | `knowledge/eclassone.md` | ✅ |
| EPayRoll | `knowledge/epayroll.md` | ✅ |
| Converso | `knowledge/converso.md` | ❌ Pendiente |
| Casos de éxito | `knowledge/casos_exito.md` | ✅ |
| FAQs | `knowledge/faqs.md` | ✅ |

### Por cada producto debe responder

- ¿Qué problema resuelve?
- ¿A quién se le vende?
- ¿Qué sectores aplican?
- ¿Qué mensajes comerciales usar?
- ¿Qué CTA corresponde?
- ¿Qué landing usar?
- ¿Qué objeciones frecuentes existen?
- ¿Qué beneficios destacar?

### Sectores objetivo

Educación · Retail · RRHH · Manufactura · Servicios · Salud · Gobierno · Contabilidad

### Estructura por artículo (MD)

```markdown
## Problema
## Explicación
## Solución
## Recomendación
## CTA
```

Framework de contenido: **Problema → Explicación → Solución → Recomendación**

---

## 3. Archivos del sistema

### Existentes (iniciados)

```
Marketing/
  accio/
    business_context.json    ← contexto empresa editable
    editorial_rules.json     ← reglas 75/25 interina + 95/5 objetivo
  knowledge/
    manifest.json            ← catálogo de artículos
    easytech.md
    en1.md
    eposone.md
    eclassone.md
    epayroll.md
    odoo_fe.md
    casos_exito.md
    faqs.md

Motor_Tecnico/accio_engine/
  knowledge_api.py           ← módulo preparatorio (NO integrado a app.py)
```

### Pendientes

```
Marketing/knowledge/
  converso.md
  sectors.json               ← matriz sector → producto → keywords
  objections.json
  ctas.json

Marketing/accio/
  product_matrix.json        ← producto × sector × necesidad
```

### business_context.json — campos

| Campo | Ejemplo |
|-------|---------|
| empresa | Easy Technology Services |
| industria | Transformación Digital |
| pais | Panamá |
| publico_objetivo | PYMEs Panamá |
| productos_servicios | EN1, EPOSOne, Odoo+FE… |
| diferenciadores | FE+ERP integrado, diagnóstico gratis |
| problemas_que_resuelve | Procesos manuales, data desconectada |
| tono_comunicacion | Profesional, educativo, Panamá |
| objetivos_comerciales | Diagnósticos, autoridad, leads |
| cta_principal | DIAGNÓSTICO |
| contacto | email, whatsapp, guia |

### editorial_rules.json — reglas

| Regla | Valor |
|-------|-------|
| Interina (Fase C) | 3 valor + 1 venta (75/25) |
| Objetivo (Fase E) | educación 50% · consejo 20% · caso 15% · tendencia 10% · venta 5% |
| Framework | problem → explanation → solution → recommendation |
| Slots semanales | L consejo · Mi caso · Vi tendencia · Do venta |

---

## 4. knowledge_api.py (preparatorio)

Módulo en `Motor_Tecnico/accio_engine/knowledge_api.py`.

**Funciones previstas:**

| Función | Descripción |
|---------|-------------|
| `load_business_context()` | Lee contexto empresa |
| `save_business_context()` | Guarda contexto |
| `list_knowledge()` | Lista artículos KB |
| `load_article(slug)` | Carga ficha con secciones parseadas |
| `generate_topic()` | Genera post desde KB + contexto |
| `editorial_balance()` | Balance valor/venta en cola |

**Estado:** Código existe, **no integrado** a `app.py` ni dashboard. Requiere GO para activar.

---

## 5. Endpoints futuros (requieren GO)

```
GET  /accio/config/business-context
POST /accio/config/business-context
GET  /accio/knowledge
GET  /accio/knowledge/<slug>
GET  /accio/dashboard/api/knowledge
POST /accio/content/generate-topic
```

---

## 6. UI dashboard futura (requiere GO)

Tab **Conocimiento** con:

- Formulario Contexto de Negocio (editable)
- Biblioteca KB (lista + preview)
- Generador de temas (producto + tipo + preview)
- Balance editorial (valor vs venta %)

---

## 7. Criterios de cierre Fase E

- [ ] Contexto negocio editable sin tocar código
- [ ] KB con ≥8 fichas producto + Converso + sectores
- [ ] API knowledge integrada y documentada
- [ ] Dashboard tab Conocimiento operativo
- [ ] Post generado sigue Problema→Recomendación
- [ ] Matriz producto-sector-necesidad en JSON
- [ ] `knowledge_api.py` integrado a `app.py`

---

## 8. Dependencias

| Fase | Depende de E |
|------|--------------|
| F — Opportunity Engine | ✅ KB para clasificar producto |
| G — Campaign Engine | ✅ KB para copy coherente |
| D — Landings | ✅ Mensajes por producto |
| K — Agentes IA | ✅ KB como contexto base |

---

## 9. No hacer en Fase E sin GO separado

- Opportunity Engine
- Integración runtime `knowledge_api.py` → `app.py`
- Reinicio producción
- Generación automática en cron
- LLM externo (OpenAI/Ollama) — definir en GO

---

## 10. Referencias

- Roadmap: `ROADMAP.md` → Fase E
- Arquitectura: `EMACCION_ARCHITECTURE.md`
- Brecha: `EMACCION_GAP_ANALYSIS.md`
- Contexto: `CONTEXTO.md`
