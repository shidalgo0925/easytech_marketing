# Wireframe — Inicio unificado EM+Acción

**Versión:** 1.0 · **Fecha:** 2026-06-29  
**Objetivo:** Reemplazar la pestaña **Resumen** del dashboard legacy por una pantalla **Inicio** entendible en &lt;10 segundos.  
**Base:** VS1 Pantalla 1 (`plan_slice`) + datos de `dashboard/api/summary` + borradores del asistente.

---

## Principios (no negociables)

| # | Regla |
|---|--------|
| 1 | **Una pantalla = una historia:** plan → siguiente paso → señales → trabajo pendiente |
| 2 | **Un CTA principal** por estado; el resto son secundarios o enlaces |
| 3 | **Lenguaje de usuario** — sin Tenant/App duplicado, sin IDs (`linkedin_07_…`), sin “legacy”, sin scrapers |
| 4 | **Asistente integrado** — banner o tarjeta contextual; **sin columna lateral fija** |
| 5 | **Métricas CRM profundas** → pantalla **Clientes**; no en Inicio |

---

## Layout general

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TOPBAR                                                                      │
│ [EM+Acción]  [Empresa ▼]                              [Avatar · nombre]     │
└─────────────────────────────────────────────────────────────────────────────┘
┌──────────┬──────────────────────────────────────────────────────────────────┐
│ SIDEBAR  │ MAIN — scroll vertical, ancho completo (sin panel IA derecho)    │
│          │                                                                  │
│ ● Inicio │ ① SALUDO                                                       │
│   Plan   │ ② PLAN (banner activo u onboarding)                              │
│   …      │ ③ [opcional] Banner asistente                                    │
│          │ ④ SIGUIENTE PASO (tarjeta destacada)                             │
│          │ ⑤ SEÑALES (4 preguntas, grid 2×2)                              │
│          │ ⑥ TRABAJO PENDIENTE (2 columnas)                                 │
│          │                                                                  │
└──────────┴──────────────────────────────────────────────────────────────────┘
```

**Qué desaparece respecto al Resumen actual**

- 10 pestañas horizontales en esta vista (quedan en sidebar reducido)
- 7 KPIs de colores iguales
- Tabla “Leads CRM” completa
- Tabla “Órdenes del motor”
- Banner “Tenant · App”
- Botón global “Publicar siguiente” en header
- Panel lateral “Asistente EM+Acción” (30% ancho)

---

## Zona ① — Saludo

```
Buenos días, Shidalgo
Tu prioridad hoy: avanzar «Plan Q3 2026 — Lanzamiento EN1».
```

| Campo | Fuente | Notas |
|-------|--------|-------|
| Nombre | sesión `user_name` | Solo primer nombre |
| Subtítulo | plan activo | Si no hay plan: *«Empieza definiendo tu plan de marketing.»* |

---

## Zona ② — Plan (banner)

### Estado A — Sin plan activo

```
┌────────────────────────────────────────────────────────────┐
│ ¿Cuál es tu objetivo este trimestre?                       │
│ Define qué quieres lograr antes de publicar o proponer     │
│ acciones concretas.                                        │
│                                                            │
│                    [ Crear tu primer plan ]                │
└────────────────────────────────────────────────────────────┘
```

### Estado B — Plan activo

```
┌────────────────────────────────────────────────────────────┐
│ ● Plan Q3 2026 — Lanzamiento EN1                           │
│   En curso desde 2026-06-15 · Meta: 12 reuniones/mes      │
│                                    [ Ver detalle ]         │
└────────────────────────────────────────────────────────────┘
```

`Ver detalle` → pantalla Activar Plan (solo lectura si ya activo) o resumen del plan.

---

## Zona ③ — Banner asistente (condicional)

**Solo si** OpenAI Key no configurada **y** el usuario puede editar configuración.

```
┌────────────────────────────────────────────────────────────┐
│ ✦ ¿Quieres recomendaciones personalizadas?                 │
│   Activa el asistente en Configuración para recibir        │
│   propuestas alineadas a tu negocio.                       │
│                              [ Configurar asistente ]      │
└────────────────────────────────────────────────────────────┘
```

**No mostrar:** badge “sin OpenAI Key” en topbar · caja roja permanente · chat vacío.

Si la key **sí** está: esta zona no aparece (el asistente se usa vía “Siguiente paso” o chat bajo demanda).

---

## Zona ④ — Siguiente paso (motor de prioridad)

Una tarjeta. **Un título + una descripción + un botón primario** (+ secundario opcional).

### Árbol de decisión (orden de prioridad)

```
1. ¿Borrador del asistente pendiente de aprobar?
   → SÍ: "Revisa la publicación sugerida" → [ Aprobar y encolar ]

2. ¿Publicación en cola lista para revisar/publicar? (estado programado o listo)
   → SÍ: "Tienes una publicación lista" → [ Revisar publicación ]

3. ¿Sin plan activo?
   → SÍ: "Define tu plan de marketing" → [ Crear plan ]

4. ¿Plan activo sin propuestas generadas?
   → SÍ: "Elige tu próximo movimiento estratégico" → [ Ver opciones estratégicas ]
        Secundario: [ Ver contexto ]

5. ¿Propuestas generadas sin decisión?
   → SÍ: "Tienes propuestas por revisar" → [ Ver propuestas ]

6. ¿Contexto &lt; 50%?
   → SÍ: "Completa tu contexto" → [ Completar contexto ]

7. DEFAULT (todo al día)
   → "Todo en orden por ahora" → [ Ver calendario editorial ]
```

### Ejemplo visual — prioridad publicación

```
┌────────────────────────────────────────────────────────────┐
│ SIGUIENTE PASO                                             │
│                                                            │
│ Tienes una publicación lista para LinkedIn                 │
│ Revisa el texto y confirma si quieres publicarla hoy.    │
│                                                            │
│ [ Revisar publicación ]    [ Ver calendario ]              │
└────────────────────────────────────────────────────────────┘
```

`Revisar publicación` → modal o pantalla **Publicar** (split: preview + Aprobar / Editar / Rechazar).

---

## Zona ⑤ — Señales (4 preguntas)

Grid 2×2. Cada tarjeta: **pregunta** (título) · **respuesta corta** (número o %) · **frase humana** (subtítulo).

| Pregunta | Respuesta | Subtítulo (ejemplos) |
|----------|-----------|----------------------|
| ¿Qué publicaciones están pendientes? | `1` | Una publicación espera tu revisión |
| ¿Cuántos prospectos tienes en marketing? | `175` | 175 prospectos en etapa comercial |
| ¿Hay propuestas por decidir? | `0` | Aún no has generado propuestas para este plan |
| ¿Qué tan completo está tu contexto? | `68%` | Puedes proponer, pero conviene completar más fuentes |

**Interacción:** clic en tarjeta → pantalla relacionada (Publicaciones, Clientes, Propuestas, Contexto).

**No incluir en Inicio:** Prospectos CSV, FB/IG como fracción, Órdenes pendientes, Publicados totales.

---

## Zona ⑥ — Trabajo pendiente

Dos columnas iguales. Máximo **6 ítems** por lista; enlace “Ver todo” si hay más.

### Columna izquierda — Cola de publicaciones

```
Cola de publicaciones
────────────────────────────────────────
Las PYME en Panamá enfrentan un reto…
LinkedIn · Programada · 28 jun 2026

Demo de plataformas — copy corto…
Facebook · Pendiente de revisión · 30 jun

[ Ver todas las publicaciones ]
```

| Mostrar | Ocultar |
|---------|---------|
| Primeras líneas del copy como título | `linkedin_07_demo_plataformas` |
| Canal · estado humano · fecha | “Programado (legacy)” |
| Clic → detalle publicación | Columna “Vista previa” duplicada |

### Columna derecha — Pendientes de decisión

**Fusiona** planes en borrador + borradores del asistente (antes en sidebar).

```
Pendientes de tu atención
────────────────────────────────────────
[Borrador IA] Publicación LinkedIn
Sugerida hoy · sobre facturación electrónica
                    [ Revisar ]

Plan Q2 borrador
Guardado el 2026-06-10
                    [ Activar ]

[ Crear plan ]
```

| Tipo ítem | Acción |
|-----------|--------|
| `assistant_draft` | Revisar → modal aprobar/rechazar |
| `plan_borrador` | Activar → pantalla Activar |
| Vacío | CTA “Crear plan” |

**Quitar de Inicio:** tabla completa Leads CRM (mover a **Clientes** con enlace “Abrir pipeline”).

---

## Sidebar — navegación reducida

```
● Inicio
  Plan
  Contexto
  Propuestas
  ─────────
  Publicar      → cola + calendario + flyers (futuro: un módulo)
  Clientes      → leads Odoo + métricas conversión
  Conocimiento
  Conectores
  Configuración
```

Inicio es **home** post-login. Las 10 pestañas del dashboard legacy se agrupan; no compiten con el flujo vertical del plan.

---

## Topbar

| Elemento | Inicio unificado |
|----------|------------------|
| Logo | Link a Inicio (no a dashboard legacy) |
| Selector empresa | Una sola vez (sin banner Tenant/App) |
| Selector app | Solo si tenant tiene &gt;1 app; dentro del pill o submenú empresa |
| “Actualizar” | Opcional · icono discreto o pull-to-refresh |
| “Publicar siguiente” | **Eliminado** — lo sustituye Siguiente paso |
| Avatar | Menú: perfil · cerrar sesión |

---

## Asistente — comportamiento fuera del sidebar

| Momento | UI |
|---------|-----|
| Sin API key | Banner zona ③ |
| Borrador generado | Ítem en columna derecha + puede ser Siguiente paso #1 |
| Chat libre | Botón flotante discreto o entrada en Configuración → “Probar asistente” |
| Aprobar/rechazar | Modal centrado; no panel permanente |

```
┌─────────────────────────────────────────┐
│ Revisar publicación sugerida        [×] │
│─────────────────────────────────────────│
│ [preview del post]                      │
│                                         │
│ [ Rechazar ]  [ Editar ]  [ Aprobar → cola ] │
└─────────────────────────────────────────┘
```

---

## Mapa de datos (APIs existentes)

| Zona | Endpoint / fuente |
|------|-------------------|
| Plan activo | `GET /api/v1/.../marketing-plans/active` |
| Planes borrador | `GET /api/v1/.../marketing-plans/{id}` + filtro `borrador` |
| Cola publicaciones | `GET /accio/{tenant}/dashboard/api/summary` → `pending_posts` |
| Prospectos marketing | `summary.odoo.marketing_stage` |
| Contexto % | `GET /api/v1/.../marketing-context` → `computeConfidence()` |
| Propuestas | `POST /api/v1/.../planner/proposals` (cache local o última sesión) |
| Borradores asistente | `GET /accio/{tenant}/dashboard/api/assistant/orders` (pendiente aprobar) |
| Estado OpenAI | `GET .../assistant/status` |

---

## Estados de pantalla (matriz QA)

| # | Escenario | Siguiente paso esperado | Señales |
|---|-----------|-------------------------|---------|
| 1 | Usuario nuevo, sin plan | Crear plan | Contexto — · Propuestas 0 |
| 2 | Plan activo, contexto bajo | Completar contexto | % bajo |
| 3 | Plan + contexto OK, sin propuestas | Ver opciones estratégicas | Propuestas 0 |
| 4 | 1 post en cola | Revisar publicación | Pendientes 1 |
| 5 | Borrador IA pendiente | Aprobar publicación (prioridad sobre post) | — |
| 6 | Todo al día | Ver calendario | Nada pendiente |

---

## Antes → Después (captura actual)

| Hoy (confuso) | Inicio unificado |
|---------------|------------------|
| 7 KPIs mismo peso visual | 4 señales con pregunta |
| Leads CRM en Inicio | Enlace desde señal → Clientes |
| Asistente 30% ancho | Banner + tarjeta + modal |
| `linkedin_07_demo_plataformas` | Título = primeras palabras del copy |
| Publicar siguiente (header) | Siguiente paso contextual |
| 10 tabs | Sidebar 9 ítems agrupados |

---

## Implementación sugerida (fases)

1. **Ya hecho (~80%):** `plan_slice.html` pantalla Workspace — extender `renderNextAction()` con árbol de prioridad completo.
2. **Quick:** fusionar borradores asistente en columna derecha (`assistant/orders`).
3. **Quick:** hacer tarjetas de señales clicables.
4. **Medio:** modal revisar publicación (extraer lógica del sidebar actual de `dashboard.html`).
5. **Después:** redirect login → `/accio/plan/{tenant}/`; Resumen legacy → “Vista avanzada” o deprecar.

---

## Criterio de aceptación UX

Un administrador de marketing sin formación técnica debe poder responder en 10 s:

1. ¿Tengo un plan activo?
2. ¿Qué me toca hacer ahora?
3. ¿Hay algo urgente en publicaciones o propuestas?

Si necesita leer IDs, estados “legacy” o elegir entre 7 números sin contexto → **no pasa**.
