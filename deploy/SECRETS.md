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
| `META_APP_ID` | App Meta Developers |
| `META_APP_SECRET` | App Meta |
| `META_PAGE_ACCESS_TOKEN` | Token pagina FB |
| `META_IG_USER_ID` | Instagram Business ID |
| `OPENAI_API_KEY` | Asistente IA conversacional (OpenAI, `sk-…`) — **no** es `ACCIO_API_KEY` |
| `OPENAI_MODEL` | Modelo OpenAI (default: `gpt-4o-mini`) |
| `AI_ASSISTANT_ENABLED` | `true` / `false` — activar asistente IA globalmente |

## Backup recomendado

```bash
# Secretos (.env, deploy/secrets)
./scripts/backup_secrets.sh

# Base Marketing OS (marketing_os.db)
./scripts/backup_marketing_os_db.sh

# Copia manual rápida
cp /opt/easytech_marketing/.env ~/backups/easymarketingone.env.$(date +%Y%m%d)
chmod 600 ~/backups/easymarketingone.env.*
```

## Marketing OS (Bloque 1)

| Variable | Uso |
|----------|-----|
| `ACCIO_PLATFORM_DB` | Ruta SQLite plataforma (default: `Marketing/platform/marketing_os.db`) |
| `ACCIO_MEMORY_STORE` | `sql` en prod |
| `ACCIO_BRAIN_STORE` … `ACCIO_LEAD_STORE` | `dual` — JSON legacy + SQLite |

Config prod estructural: `deploy/secrets/.env.prod` (sin API keys). Secretos en `.env` raíz.

Migración: `./scripts/run_marketing_os_migrations.sh` · Verificación: `./scripts/verify_marketing_os_prod.py`

Rotar `ACCIO_API_KEY` y API key Odoo si se expusieron en chat.
