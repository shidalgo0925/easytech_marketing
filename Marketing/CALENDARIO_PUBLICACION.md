# Calendario de publicación — Operación ArrozConPollo

## Modo automatico (LinkedIn)

Cola: `Marketing/content_queue.json`  
Script: `Motor_Tecnico/linkedin_publisher.py`  
n8n: `docs/n8n-workflow-linkedin.json` (Mar/Jue 8:00 AM Panama)

| Post | Fecha programada | Estado |
|------|------------------|--------|
| #1 FE + Odoo | 2026-06-19 13:00 | pending |
| #2 Diagnóstico | 2026-06-23 13:00 | pending |

Setup: ver `docs/LINKEDIN_AUTOMATIZACION.md`

## Manual (Instagram / Facebook — pendiente API Meta)

| Día | Red | Contenido | Archivo |
|-----|-----|-----------|---------|
| Mar tarde | Instagram | Mismo mensaje, flyer #3 | `Instagram/post_01_facturacion_electronica.md` |
| Mié | Facebook | Post #1 adaptado | `Facebook/post_01_facturacion_electronica.md` |
| Vie | Instagram Stories | 3 frames diagnóstico | `Instagram/post_01_facturacion_electronica.md` (Stories) |

## Checklist

- [ ] Token LinkedIn en `.env` (una sola vez)
- [ ] Flyers PNG en `Marketing/flyers/`
- [ ] Workflow n8n importado y activo
- [ ] Responder comentarios/DMs en < 24 h
- [ ] Lead "DIAGNÓSTICO" → Odoo CRM, etapa Nuevo - Marketing

## Próximos (semana 2)

- LinkedIn Post #3: "Implementamos Odoo" (flyer #2)
- LinkedIn Post #4: Demo plataformas sin costo (flyer #12)
