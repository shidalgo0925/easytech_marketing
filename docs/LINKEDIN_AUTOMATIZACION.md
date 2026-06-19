# Publicacion automatica en LinkedIn

El motor publica solo desde la cola `Marketing/content_queue.json`.
Tu NO copias/pegas cada post.

## Que hace el sistema

1. **Cola** (`Marketing/content_queue.json`) — posts con fecha/hora y estado `pending` / `published`
2. **Script** (`Motor_Tecnico/linkedin_publisher.py`) — publica el siguiente post listo + flyer + primer comentario
3. **n8n** — ejecuta el script martes y jueves 8:00 AM (Panama)

## Configuracion unica (15 min, una sola vez)

LinkedIn exige autorizar tu cuenta. No se puede evitar.

### Paso 1 — App en LinkedIn Developers

1. Entra a https://www.linkedin.com/developers/apps
2. **Create app** → asocia tu pagina EasyTech si la tienes
3. En **Products**, solicita **Share on LinkedIn** (permiso `w_member_social` para perfil personal)
4. Si publicas como **empresa**, solicita **Marketing Developer Platform** (`w_organization_social`)
5. Copia **Client ID** y **Client Secret**

### Paso 2 — Obtener token y URN

Opcion A (recomendada): usar n8n con nodo LinkedIn OAuth2 y copiar el token a `.env`

Opcion B: OAuth manual con redirect URL de tu app:
- Redirect: `https://n8n.etsrv.site/rest/oauth2-credential/callback`
- Scopes: `openid profile w_member_social` (perfil) o `w_organization_social` (empresa)

Obtener tu **author URN**:
```bash
curl -H "Authorization: Bearer TU_TOKEN" \
  "https://api.linkedin.com/v2/userinfo"
```
El `sub` da el person ID → `urn:li:person:SUB`

Para pagina de empresa:
```bash
curl -H "Authorization: Bearer TU_TOKEN" \
  "https://api.linkedin.com/v2/organizationAcls?q=roleAssignee"
```

### Paso 3 — Variables en `.env`

```bash
LINKEDIN_ACCESS_TOKEN=tu_token_largo
LINKEDIN_AUTHOR_URN=urn:li:person:XXXX
```

### Paso 4 — Flyers

Sube los PNG a:
```
/opt/easytech_marketing/Marketing/flyers/03_facturacion_electronica.png
/opt/easytech_marketing/Marketing/flyers/11_diagnostico_gratuito.png
```
Si no hay imagen, publica solo texto.

### Paso 5 — Importar workflow en n8n

1. Abre https://n8n.etsrv.site
2. **Workflows → Import from File** → `docs/n8n-workflow-linkedin.json`
3. Activa el workflow (toggle ON)

## Probar antes de automatizar

```bash
cd /opt/easytech_marketing
source venv/bin/activate

# Ver que post saldria (sin publicar)
python3 Motor_Tecnico/linkedin_publisher.py --dry-run

# Publicar ahora ignorando la fecha (cuando .env este listo)
python3 Motor_Tecnico/linkedin_publisher.py --force
```

## Agregar mas posts

Edita `Marketing/content_queue.json` — copia un bloque, cambia `id`, `scheduled_at`, `text`, `status: pending`.

## Limitaciones honestas

| Que es automatico | Que NO lo es |
|-----------------|--------------|
| Publicar en fecha/hora | Crear app LinkedIn (1 vez) |
| Adjuntar flyer si existe | Subir flyers PNG al servidor |
| Primer comentario 2 min despues | Responder DMs/comentarios de clientes |
| Actualizar cola a `published` | Renovar token si expira (~60 dias) |

Instagram/Facebook requieren Meta Business API aparte (proximo paso si lo necesitas).
