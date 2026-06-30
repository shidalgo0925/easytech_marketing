# VS2 — Primera campaña publicada

**Estado:** Activo · **Objetivo:** cerrar el flujo visible Oportunidad → LinkedIn desde la consola.

---

## Flujo visible

```
Pipeline → Oportunidad → Recomendación → Campaña → Contenido
    → Aprobar → Enviar a cola → Publicar ahora → Publicado
```

Consola: `/accio/plan/easytech/`

**Regla:** nada se publica sin acción humana explícita (aprobar → cola → publicar).

---

## Componentes

| Pieza | Ubicación |
|-------|-----------|
| Content approval + publish states | `content_engine_domain/` · schema **v16** |
| Publisher bridge | `content_engine_infrastructure/content_publisher_bridge.py` |
| Safe mode flags | `publish_config.py` |
| Memory audit | `content_engine_infrastructure/memory_bridge.py` |
| API | `/content/{id}/queue`, `/publish-now`, `/reject`, `/queue` (list) |
| Consola | `plan_slice.js` — botones por estado |

---

## API

Base: `/api/v1/tenants/{tenant}/content`

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/{id}/approve` | Aprobar contenido |
| POST | `/{id}/reject` | Rechazar (`{ "reason": "..." }`) |
| POST | `/{id}/queue` | Enviar a cola legacy |
| POST | `/{id}/publish-now` | Publicar (`{ "dry_run": true }` opcional) |
| GET | `/queue` | Listar queued / publishing / failed / published |
| GET | `/{id}/history` | Auditoría local (`content_history`) |

Respuesta `publish-now`:

```json
{
  "content_id": "...",
  "status": "published",
  "channel": "linkedin",
  "published_at": "...",
  "external_post_id": "...",
  "external_url": "...",
  "dry_run": false,
  "error_message": null
}
```

---

## Estados de contenido

`draft` · `pending_approval` · `approved` · `rejected` · `queued` · `publishing` · `published` · `failed` · `archived`

---

## Flags de seguridad

| Variable | Default | Efecto |
|----------|---------|--------|
| `ACCIO_PUBLISH_ENABLED` | `true` | `false` → bloquea publicación |
| `ACCIO_LINKEDIN_PUBLISH_ENABLED` | `true` | `false` → bloquea LinkedIn |
| `ACCIO_PUBLISH_DRY_RUN` | `false` | `true` → simula sin API LinkedIn |

---

## Probar en dry-run

```bash
export ACCIO_PUBLISH_DRY_RUN=true
# o en API:
curl -X POST .../content/{id}/publish-now -d '{"dry_run": true}'
```

---

## Probar publicación real

1. Credenciales LinkedIn en Conectores (`LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_AUTHOR_URN`).
2. `ACCIO_PUBLISH_DRY_RUN=false`
3. Contenido con `flyer_ref` válido en `Marketing/flyers/`.
4. Flujo consola: Aprobar → Enviar a cola → Publicar ahora.

El bridge encola en `Marketing/tenants/{tenant}/apps/{app}/content_queue.json` e invoca `linkedin_publisher.py`.

---

## Rollback

- Contenido en `failed`: corregir error y **Reintentar** desde consola.
- Cola JSON: editar `content_queue.json` manualmente si hace falta.
- Desactivar publicación: `ACCIO_PUBLISH_ENABLED=false`.

---

## Limitaciones VS2

- Solo **LinkedIn** (un canal).
- Sin Instagram, Meta, scheduler, analytics, automation.
- Publisher legacy — no reescrito; adaptador `ContentPublisherBridge`.
- Aprobación de contenido **propia** del Content Engine (no reutiliza Approval Queue de recomendaciones).

---

## Tests

```bash
./venv/bin/python3 -m unittest tests.test_vs2_content_publish -v
```
