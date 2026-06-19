# Accio Work (Desktop) + ArrozConPollo (VPS)

**No instales Accio Work en el servidor Linux.** Accio Work es app de escritorio (Windows/Mac).  
ArrozConPollo es el **motor de ejecución**. Juntos forman lo mismo que ves en tu captura.

---

## Arquitectura (como tu screenshot)

```
┌─────────────────────────────┐         HTTPS + API Key
│  ACCIO WORK (tu PC)         │ ──────────────────────────────┐
│  · Chat / Agentes           │                               │
│  · Tareas programadas       │                               ▼
│  · Entregables / archivos   │              ┌────────────────────────────┐
│  · Plugins / MCP            │              │  ARROZCONPOLLO (VPS)       │
└─────────────────────────────┘              │  · accio_engine API        │
         │                                    │  · Dashboard web         │
         │ navegador                          │  · Cron (auto publish)   │
         ▼                                    │  · Odoo / LinkedIn / CSV │
┌─────────────────────────────┐              └────────────────────────────┘
│  Dashboard operaciones      │
│  n8n.etsrv.site/accio/      │
│  dashboard/                 │
└─────────────────────────────┘
```

| Panel Accio Work | Equivalente en ArrozConPollo |
|------------------|------------------------------|
| Chat / agentes | **Accio Work** (sigue en tu PC) |
| Tareas | `GET /accio/tasks` + `Marketing/accio/tasks.json` |
| Entregables / archivos | `GET /accio/files/tree` — Marketing/, Motor_Tecnico/ |
| Ejecutar (pipeline, publicar) | API `/accio/run/*` o Dashboard botones |
| Tareas programadas | Cron en VPS (ya activo) |

**Cursor no entra en este flujo.**

---

## Paso 1 — Conectar Accio Work al motor (5 min)

En **Accio Work Desktop**:

1. Abre **Plugins** o **MCP Servers**
2. Añade servidor HTTP personalizado o Skill con estas URLs:

| Acción | Método | URL |
|--------|--------|-----|
| Estado | GET | `https://n8n.etsrv.site/accio/status` |
| Tareas | GET | `https://n8n.etsrv.site/accio/tasks` |
| Archivos | GET | `https://n8n.etsrv.site/accio/files/tree` |
| Leer archivo | GET | `https://n8n.etsrv.site/accio/files/read?path=Marketing/content_queue.json` |
| Agregar post | POST | `https://n8n.etsrv.site/accio/content/queue` |
| Prospectar | POST | `https://n8n.etsrv.site/accio/run/pipeline` |
| Publicar | POST | `https://n8n.etsrv.site/accio/run/publish-linkedin` |

3. **Header en todas las peticiones:**
   ```
   Authorization: Bearer <ACCIO_API_KEY>
   ```
   (valor en `/opt/easytech_marketing/.env` del VPS)

4. OpenAPI para importar: **https://n8n.etsrv.site/accio/openapi.json**

---

## Paso 2 — Prompt del agente en Accio Work

Crea un agente **"EasyTech Marketing — ArrozConPollo"** y pega:

```
Eres el operador de marketing de EasyTech. NO uses Cursor.

Motor remoto: https://n8n.etsrv.site/accio/
Auth: Bearer <ACCIO_API_KEY>

Antes de recomendar acciones, consulta GET /accio/status y GET /accio/tasks.
Para publicar contenido usa POST /accio/content/queue.
Para ejecutar prospectar: POST /accio/run/pipeline.
Para publicar LinkedIn: POST /accio/run/publish-linkedin.

Flyers en VPS: Marketing/flyers/ (ver manifest.json vía /accio/files/read).
CTA: DIAGNÓSTICO · +507 6688-4938 · https://n8n.etsrv.site/guia/
```

---

## Paso 3 — Tareas programadas en Accio Work

En **Tareas programadas** de Accio Work puedes pedir:

| Frecuencia | Acción API |
|------------|------------|
| Semanal | `POST /accio/run/pipeline` |
| Tras generar posts | `POST /accio/content/queue` con JSON |
| Revisión | `GET /accio/status` |

**Nota:** el VPS **ya** publica LinkedIn y prospecta por cron. Accio Work complementa; no duplica.

---

## Paso 4 — Sincronizar archivos (opcional)

Tu Accio Work tiene `Marketing/`, `Motor_Tecnico/`, `Roadmap` **locales**.

**Fuente de verdad en producción:** el VPS `/opt/easytech_marketing/`.

Opciones:

| Opción | Cómo |
|--------|------|
| **A. Solo VPS** | Accio Work lee/escribe vía API (`/accio/files/*`, `/accio/content/queue`) |
| **B. Git** | Repo privado; push desde Accio Work, pull en VPS |
| **C. rsync** | Script semanal PC → VPS |

Recomendación: **A** — Accio genera JSON de posts y los envía por API; no copies archivos a mano.

---

## Dashboard web (panel derecho de tu captura)

Para **métricas y botones** sin chat:

**https://n8n.etsrv.site/accio/dashboard/**

Ahí ves cola, leads Odoo, órdenes — como el panel de tareas/entregables pero en vivo del servidor.

---

## Lo que NO es posible (hoy)

| Expectativa | Realidad |
|-------------|----------|
| Instalar Accio Work **dentro** del VPS Linux | No — es app desktop Alibaba |
| Clonar 100% la UI Accio Work en el navegador | Meses de desarrollo |
| Reemplazar Accio Work por n8n solo | n8n no tiene chat/agentes como Accio |

---

## Flujo diario SIN Cursor

1. **Accio Work** (PC) — estrategia, posts, campañas → API al VPS  
2. **Dashboard** (navegador) — revisar cola y leads  
3. **Odoo** — pipeline comercial  
4. **Tú** — DMs LinkedIn y cierre  

El VPS ejecuta solo entre medias.

---

## Verificar conexión

Desde tu PC (PowerShell o terminal):

```bash
curl -s -H "Authorization: Bearer TU_API_KEY" \
  https://n8n.etsrv.site/accio/tasks | head -20
```

Si ves el JSON de tareas → Accio Work puede usar el mismo endpoint.

---

## Siguiente mejora (si quieres)

- Skill OpenClaw/MCP oficial apuntando a ArrozConPollo  
- Chat embebido en dashboard (Open WebUI en VPS) — **duplica** Accio Work; solo si no quieres desktop  

Por ahora: **Accio Work + API ArrozConPollo** = la experiencia de tu screenshot con ejecución real en el servidor.
