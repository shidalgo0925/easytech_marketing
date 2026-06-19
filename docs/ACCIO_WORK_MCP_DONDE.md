# Dónde está MCP en Accio Work (y qué hacer si no lo ves)

En Accio Work **no hay un botón que diga "MCP"** en el menú lateral. Es normal.

---

## Dónde buscar (3 pestañas de tu captura)

| Pestaña | Qué es | ¿MCP? |
|---------|--------|-------|
| **Plugins** | Integraciones (GitHub, Airtable…) | MCP se configura **al crear un Plugin personalizado** (no en la lista) |
| **Habilidades** | Skills del agente | Aquí subes la skill de EasyTech ✅ **recomendado** |
| **Conectores** | Gmail, Slack, Notion (OAuth) | No es MCP — son apps pre-hechas |

Según Accio Work v0.14+: *"MCP Servers support custom Server injection via **Plugin**"*.

---

## Opción A — Habilidad (la más fácil, sin MCP)

1. En Accio Work → pestaña **Habilidades**
2. **Crear** o **Subir** skill local
3. Sube este archivo del VPS:
   ```
   /opt/easytech_marketing/Marketing/accio/skill-easytech-arrozconpollo.md
   ```
   (cópialo a tu PC o descárgalo por SFTP)
4. En tu agente **EasyTech Marketing** → añade esa habilidad
5. En el chat dile tu **ACCIO_API_KEY** una vez:
   > "Mi API Key de ArrozConPollo es: xxxxx"

El agente usará HTTP para llamar al motor (Accio Work puede ejecutar peticiones web).

---

## Opción B — Plugin con MCP (avanzado)

Solo si Accio te deja **crear Plugin personalizado**:

1. **Plugins** → botón **+** / **Crear plugin** (arriba a la derecha, no en la lista de Shippo/GitHub)
2. Busca opción **MCP Server** o **Custom server URL**
3. Necesitas un servidor **MCP real** (protocolo especial), no solo REST

**Hoy ArrozConPollo expone REST** (`/accio/...`), no MCP nativo. Por eso la Opción A es mejor hasta montar un puente MCP.

---

## Opción C — Sin plugin: Dashboard (ya funciona)

No necesitas MCP ni skill para **ver y ejecutar**:

**https://n8n.etsrv.site/accio/dashboard/**

- Cola de posts
- Leads Odoo  
- Botones Pipeline / Publicar

---

## Opción D — Tareas programadas en Accio Work

Menú lateral → **Tareas programadas**

Crea tarea en lenguaje natural, por ejemplo:

> "Cada lunes a las 9am, llama a POST https://n8n.etsrv.site/accio/run/pipeline con Authorization Bearer [API_KEY]"

(Requiere que el agente tenga permiso de red.)

---

## Resumen

| Quieres | Haz esto |
|---------|----------|
| No ver MCP | Normal — usa **Habilidades** |
| Conectar ArrozConPollo | Skill `skill-easytech-arrozconpollo.md` |
| Panel visual | **Dashboard** en el navegador |
| MCP técnico después | Montamos puente MCP en VPS (Fase 2) |

**Cursor: no.**

---

## Copiar skill a tu PC (desde SSH una vez)

```bash
scp papichulo@95.111.244.137:/opt/easytech_marketing/Marketing/accio/skill-easytech-arrozconpollo.md ~/Desktop/
```

Luego súbela en Accio Work → Habilidades.
