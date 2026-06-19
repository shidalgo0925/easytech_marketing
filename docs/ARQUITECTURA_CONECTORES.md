# Arquitectura de conectores — EasyMarketingOne

## Principio

**Estructura primero, APIs después.**

1. Definir canales en `Marketing/accio/connectors.json`
2. Encolar contenido en `Marketing/content_queue.json` (`platform` por canal)
3. Orquestar desde Accio Engine + Dashboard
4. Implementar OAuth y API por fase (D.1b, D.2b, …)

## Capas

```
Marketing/accio/connectors.json     ← registro (fuente de verdad)
Marketing/content_queue.json      ← cola unificada multicanal
Motor_Tecnico/channel_publisher.py ← router por conector
Motor_Tecnico/connectors/         ← registry, queue_tools, stubs
Motor_Tecnico/*_publisher.py      ← implementaciones live
Motor_Tecnico/*_oauth.py          ← OAuth cuando aplique
Marketing/publish_logs/*.json       ← log por canal
```

## Modos de implementación

| Modo | Significado |
|------|-------------|
| `live` | Publisher real; requiere OAuth/env para publicar |
| `stub` | Cola + dry-run OK; API pendiente (no publica) |

## Añadir API a un canal stub

1. Crear OAuth (si aplica) y variables en `.env`
2. Implementar lógica en `Motor_Tecnico/connectors/publishers/<canal>.py`
3. Cambiar en `connectors.json`: `"implementation": "live"`
4. Probar: `python3 Motor_Tecnico/channel_publisher.py --connector=<id> --dry-run`

## API Accio

- `GET /accio/connectors` — registro + estado runtime
- `POST /accio/run/publish-channel` — `{"connector":"youtube","dry_run":true}`

## Dashboard

Pestaña **Conectores** — modo `live` / `stub`, cola, link OAuth o doc.
