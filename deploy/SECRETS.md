# Secretos — NO subir a Git

Guardar **fuera del repositorio** (gestor de contraseñas, vault, backup cifrado).

## Archivo principal

`/opt/easytech_marketing/.env`

## Variables

| Variable | Uso |
|----------|-----|
| `ACCIO_API_KEY` | Dashboard + API Accio Engine |
| `ACCIO_ENGINE_PORT` | Default 8092 |
| `ODOO_URL` | CRM |
| `ODOO_DB` | Base de datos |
| `ODOO_USER` | Usuario API |
| `ODOO_PASSWORD` | API key Odoo |
| `LINKEDIN_CLIENT_ID` | App LinkedIn |
| `LINKEDIN_CLIENT_SECRET` | App LinkedIn |
| `LINKEDIN_ACCESS_TOKEN` | Token OAuth |
| `LINKEDIN_AUTHOR_URN` | urn:li:person:... |

## Backup recomendado

```bash
# En el VPS (copia cifrada local, NO a GitHub)
cp /opt/easytech_marketing/.env ~/backups/easymarketingone.env.$(date +%Y%m%d)
chmod 600 ~/backups/easymarketingone.env.*
```

Rotar `ACCIO_API_KEY` y API key Odoo si se expusieron en chat.
