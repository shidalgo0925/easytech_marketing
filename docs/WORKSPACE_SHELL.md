# EM+Acción — Workspace Shell

**Estado:** APROBADO · **Opción A**  
**Fecha decisión:** 2026-06-26  
**Principio permanente:** EM+Acción tiene exactamente **un shell de navegación**. Todo el producto crece dentro de ese shell.

---

## Decisión

EM+Acción es un **Workspace**, no una colección de pantallas, wizards ni módulos independientes.

Todo ocurre dentro de un único shell:

```
┌─────────────────────────────────────────────────────────┐
│ Topbar (fija, inmutable)                                │
├─────────────────────────────────────────────────────────┤
│ Banner estrategia (discreto, persistente)               │
├──────────┬──────────────────────────────────────────────┤
│ Sidebar  │ Área de contenido (vistas dinámicas)         │
│ (producto│                                              │
│  no flujo│                                              │
└──────────┴──────────────────────────────────────────────┘
```

---

## Reglas de producto

### 1. Sidebar = producto, no flujo

Navegación libre. La app guía si falta un paso previo; **no oculta** navegación.

| Área | Rol |
|------|-----|
| Inicio | Workspace / resumen operativo |
| Plan | Estrategia (vistas internas) |
| Contexto | Fuentes para la IA — consultable siempre |
| Propuestas | Historial, comparación, aprobación |
| Publicaciones | Cola editorial |
| Clientes | Pipeline comercial |
| Operaciones | Ejecución diaria (mismo shell) |
| Configuración | Tenant, IA, conectores |

### 2. Plan = área estratégica

El wizard es **una vista**, no un módulo.

```
Plan
├── Resumen
├── Crear
├── Editar
└── Historial
```

### 3. Topbar única e inmutable

Solo contexto global, nunca cambia por pantalla:

- Logo
- Tenant
- App
- Plan activo
- IA activa
- Usuario

### 4. Banner persistente

Debajo de la topbar, discreto:

```
Plan: Q3 2026 — Generación de Leads · Estado: Activo
```

### 5. Operaciones dentro del workspace

Misma experiencia espacial. La tecnología puede ser distinta (iframe legacy inicial); la experiencia no.

---

## Implementación

| Artefacto | Ubicación |
|-----------|-----------|
| Shell HTML | `Motor_Tecnico/accio_engine/static/plan_slice.html` |
| Estilos shell | `Motor_Tecnico/accio_engine/static/plan_slice.css` |
| Router vistas | `Motor_Tecnico/accio_engine/static/plan_slice.js` |
| Operaciones embebidas | `dashboard.html?embedded=1&vista=operaciones` |
| Entry URL | `/accio/plan/{tenant}/` |

### Router

- `navigateTo(area, { planView, opsTab })` — reemplaza `showScreen()`
- Áreas: `workspace`, `plan`, `context`, `proposals`, `publications`, `clients`, `operations`, `config`
- Sub-vistas Plan: `resumen`, `crear`, `historial`

### Congelado hasta cerrar shell

- Nuevas pantallas fullscreen
- Nuevos módulos con navegación independiente
- Mini-aplicaciones con topbar propia

---

## Migración VS1

| Vista VS1 | Destino en shell |
|-----------|------------------|
| Inicio | `view-workspace` |
| Crear Plan (wizard) | `plan` → `crear` |
| Activar Plan | `plan` → `resumen` |
| Context Builder | `view-context` |
| Propuestas IA | `view-proposals` |
| Dashboard Operaciones | `view-operations` (iframe embedded) |

---

## Referencias

- [ROADMAP.md](ROADMAP.md)
- [VERTICAL_SLICE_1.md](VERTICAL_SLICE_1.md)
- [sessions/2026-06-29-vs1-ux.md](sessions/2026-06-29-vs1-ux.md)
