# Fase D — Conectores multicanal

| # | Canal | Estado | Archivo / URL |
|---|-------|--------|---------------|
| D.1 | LinkedIn | ✅ Activo | `linkedin_publisher.py`, `/linkedin/` |
| D.2 | Facebook Page | 🔧 Listo (OAuth pendiente) | `meta_publisher.py`, `/meta/` |
| D.3 | Instagram Business | 🔧 Listo (OAuth pendiente) | `meta_publisher.py`, `/meta/` |
| D.4 | Google Business Profile | 📋 Planificado | — |
| D.5 | Meta Ads | 📋 Planificado | Tras D.2–D.3 |
| D.6 | Google Ads | 📋 Planificado | — |
| D.7 | YouTube | 📋 Planificado | — |
| D.8 | TikTok | 📋 Planificado | — |

## Cola unificada

Todos los canales usan `Marketing/content_queue.json` con campo `"platform"`:

- `linkedin`
- `facebook`
- `instagram`

## Dashboard

Pestaña **Conectores** → estado, cola y link OAuth.

## Próximo paso operativo

1. Crear app Meta + añadir `META_APP_ID` / `META_APP_SECRET` en `.env`
2. Autorizar en https://n8n.etsrv.site/meta/
3. Probar dry-run Facebook e Instagram
4. Activar cron Meta (opcional)

Ver `docs/META_CONECTORES.md` para detalle.
