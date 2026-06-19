# Cómo operar SIN Cursor

**Cursor no es tu herramienta de marketing.** Solo se usa si algo técnico se rompe en el servidor.

---

## Las 3 herramientas que SÍ usas

| Para qué | Herramienta | URL / dónde |
|----------|-------------|-------------|
| **Ver y ejecutar** (pipeline, publicar) | **Dashboard Accio** | https://n8n.etsrv.site/accio/dashboard/ |
| **Estrategia y contenido** (posts, calendario) | **Accio** (chat en tu PC) | Cline o Cursor **solo como chat Accio** — ver prompt abajo |
| **CRM y leads** | **Odoo** | https://easydb.etsrv.site |
| **Automatización visual** (opcional) | **n8n** | https://n8n.etsrv.site |

**El servidor trabaja solo:** cron publica LinkedIn, prospecta domingos, procesa órdenes Accio cada 15 min.

---

## Lo que NO debes hacer

| ❌ No hagas esto | ✅ Haz esto en su lugar |
|------------------|-------------------------|
| Abrir Cursor SSH para publicar un post | Dashboard → **Publicar** o esperar fecha automática |
| Pedirle a Cursor que escriba posts | Accio (chat marketing) → API `/accio/content/queue` |
| Cursor para ver leads | Odoo o Dashboard Accio |
| Cursor para prospectar | Dashboard → **Pipeline** (o espera el domingo) |
| Cursor para “encender” el motor | Ya está encendido (`easytech-accio-engine`) |

---

## Flujo diario (cero Cursor)

```
1. Abres Dashboard Accio (navegador) — 2 min
2. Revisas leads en Odoo — cuando quieras
3. Respondes DMs LinkedIn con DIAGNÓSTICO — tú (única parte humana de ventas)
4. Todo lo demás → automático en el VPS
```

---

## Cuándo SÍ usar Cursor (raro)

Solo ingeniería: EN1 roto, SSL, bug en API, nueva integración. **No marketing del día a día.**

---

## Accio en tu PC (no el servidor)

Abre **Cline** o un **chat nuevo en Cursor en tu PC** (sin SSH al VPS) y pega el prompt de:

`Marketing/accio/PROMPT_OPERADOR.md`

Accio enviará órdenes a `https://n8n.etsrv.site/accio/` con la API Key.

**Nunca abras el proyecto `/opt` en Cursor para marketing.**

---

## Automatización activa (sin tocar nada)

| Tarea | Cuándo |
|-------|--------|
| Publicar LinkedIn (si llegó fecha) | Mar y Jue 8:00 AM + Vie 13:00 Panamá |
| Scraper + Odoo | Domingos 6:00 AM |
| Procesar órdenes Accio | Cada 15 min |

---

## API Key (solo una vez por sesión de dashboard)

En el servidor: `grep ACCIO_API_KEY /opt/easytech_marketing/.env`  
O pídesela a quien administra el VPS. **No la compartas en chats públicos.**
