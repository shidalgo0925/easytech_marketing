# Restauración branding — Workspace Shell

**Fecha:** 2026-06-26  
**Decisión:** Conservar shell nuevo + recuperar ADN visual del Command Center  
**Alcance:** Solo CSS/HTML visual en `plan_slice.*` + fuente en `accio-design.css`

---

## Capturas

| Archivo | Descripción |
|---------|-------------|
| `ANTES_P1_*.png` | Workspace pre-restauración (copia de `P1_workspace_revision/`) |
| `REFERENCIA_dashboard_operaciones.png` | Dashboard legacy — referencia visual |
| `DESPUES_workspace_shell_branding.png` | Workspace shell con branding restaurado |
| `DESPUES_area_plan.png` | Área Plan dentro del shell |

Generar: `ACCIO_API_KEY=… python3 scripts/capture_branding_restoration.py`

---

## Estilos restaurados (lista exacta)

### Tipografía y marca
- **Fraunces** importada en `accio-design.css` (wordmark `EM`+Acción como dashboard)
- Logo **engranaje animado** (`.topbar-mark` + `.em-gear-ring`) en lugar del círculo genérico
- Clases `.brand-name`, `.brand-em`, `.topbar-brand` del Command Center

### Topbar
- Hereda `.topbar`: `--bg-panel`, `box-shadow: --accio-shadow-sm`, borde `1px`
- Pills **Tenant / App**: `.empresa-pill--claro` + `.empresa-pill-label` + `.empresa-select`
- Plan activo centrado: `.resumen-empresa-name` + verde corporativo
- IA y usuario: `.status-pill` (verde activo / ámbar inactivo) como dashboard

### Banner estrategia
- Clase `.resumen-empresa-banner`: fondo `--accent-bg`, borde `--border-green`
- Tipografía `.resumen-empresa-label` / `.resumen-empresa-name`

### Sidebar (equivalente vertical del navbar)
- Fondo `--bg-panel`, borde `1px`, sombra `--accio-shadow-sm`
- Ítem activo: borde izquierdo `--green-600`, fondo `--accent-bg`, peso 600 (como `.navbar .nav-item.active`)

### Área principal
- Fondo `--bg-canvas` (clase `.content`)
- Padding `--space-xl` / `--space-2xl` como dashboard

### Tarjetas y métricas
- `.vs1-card`: borde `1px`, `box-shadow: --accio-shadow-sm`
- Paneles tareas: `.panel` / `.accio-card` con `.panel-header` y `.panel-body`
- Señales: estilo `.metric-card` — `border-top: 3px solid --green-600`, label uppercase 10px
- Onboarding: tinte `--accent-bg` + borde superior verde

### Botones
- `.vs1-btn--primary` alineado a `.btn-primary` (verde 600, hover 400, peso 600)
- `.vs1-btn--secondary` / `--ghost` alineados a `.btn-ghost`

### Banner IA (capability)
- Gradiente verde sutil (como `.accio-home-banner`), borde `--border-green`

### Sub-nav Plan
- Pestañas estilo `.navbar .nav-item` (borde inferior verde en activo)

### Branding tenant
- `tenant_profile.branding_css()` extendido a `.topbar-mark`, `.brand-name`, `.brand-em`

---

## Shell — sin cambios funcionales

- Arquitectura Workspace Shell intacta
- `navigateTo()` / áreas / iframes Operaciones sin modificar
- Backend, API y dominio sin tocar (excepto inyección CSS tenant existente)

---

## Verificación manual

1. `/accio/plan/{tenant}/` — topbar con engranaje + Fraunces + pills verdes
2. Sidebar visible en todas las áreas
3. Navegar Plan → Crear, Contexto, Operaciones (iframe)
4. Comparar lado a lado con `/accio/dashboard/{tenant}/?vista=operaciones`
