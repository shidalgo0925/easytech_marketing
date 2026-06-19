# Fase D — Conectores multicanal

## Estrategia actual

**Estructura completa → APIs y permisos canal por canal.**

Ver `docs/ARQUITECTURA_CONECTORES.md`.

| # | Canal | Modo | Estado |
|---|-------|------|--------|
| D.1 | LinkedIn | live | ✅ Operativo |
| D.2 | Facebook | live | Estructura + publisher; OAuth pendiente |
| D.3 | Instagram | live | Estructura + publisher; OAuth pendiente |
| D.4 | Google Business | stub | Cola + dry-run |
| D.5 | Meta Ads | stub | Cola + dry-run |
| D.6 | Google Ads | stub | Cola + dry-run |
| D.7 | YouTube | stub | Cola + dry-run |
| D.8 | TikTok | stub | Cola + dry-run |

## Registro

`Marketing/accio/connectors.json`

## Router

```bash
python3 Motor_Tecnico/channel_publisher.py --connector=google_business --dry-run --force
```

## Cuando toque conectar APIs

| Fase | Doc |
|------|-----|
| D.2–D.3 | `docs/META_CONECTORES.md` |
| D.4 | `docs/conectores/GOOGLE_BUSINESS.md` |
| D.5 | `docs/conectores/META_ADS.md` |
| D.6 | `docs/conectores/GOOGLE_ADS.md` |
| D.7 | `docs/conectores/YOUTUBE.md` |
| D.8 | `docs/conectores/TIKTOK.md` |
