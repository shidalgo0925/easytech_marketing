# Conectar redes — Accio EasyMarketingOne

Guía rápida para activar cada canal. **LinkedIn ya está operativo.**

## Estado y URLs

| Canal | Conectar | Publisher | Cron |
|-------|----------|-----------|------|
| LinkedIn | https://n8n.etsrv.site/linkedin/ | ✅ live | Mar/Jue/Vie |
| Facebook | https://n8n.etsrv.site/meta/ | ✅ live | Mié/Vie |
| Instagram | https://n8n.etsrv.site/meta/ | ✅ live | Mié/Vie |
| Google Business | https://n8n.etsrv.site/google/ | ✅ live | Sáb |
| YouTube | https://n8n.etsrv.site/google/ | stub (video) | — |
| TikTok | https://n8n.etsrv.site/tiktok/ | stub (API) | — |
| Meta Ads / Google Ads | — | stub | — |

Dashboard → pestaña **Conectores** → enlace **Conectar**.

---

## 1. Meta (Facebook + Instagram)

1. Crear app en [developers.facebook.com](https://developers.facebook.com/apps/)
2. Agregar a `.env`:
   ```bash
   META_APP_ID=...
   META_APP_SECRET=...
   META_REDIRECT_URI=https://n8n.etsrv.site/meta/callback
   ```
3. En la app → Facebook Login → Valid OAuth Redirect URIs: la URL de arriba
4. Abrir **https://n8n.etsrv.site/meta/** → Autorizar
5. Probar dry-run:
   ```bash
   python3 Motor_Tecnico/meta_publisher.py --platform=facebook --dry-run --force
   ```

Posts en cola: `facebook_01_*`, `instagram_01_*` (fechas jul 2026).

---

## 2. Google (Business Profile + YouTube)

1. Proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. Habilitar APIs: **Business Profile**, **YouTube Data API v3**
3. OAuth consent + credenciales Web → redirect:
   `https://n8n.etsrv.site/google/callback`
4. Agregar a `.env`:
   ```bash
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   GOOGLE_REDIRECT_URI=https://n8n.etsrv.site/google/callback
   ```
5. Abrir **https://n8n.etsrv.site/google/** → Autorizar
6. Probar:
   ```bash
   python3 Motor_Tecnico/channel_publisher.py --connector=google_business --dry-run --force
   ```

YouTube comparte el mismo OAuth; subida de video es Fase D.7b.

---

## 3. TikTok

1. App en [developers.tiktok.com](https://developers.tiktok.com/) con **Content Posting** aprobado
2. `.env`:
   ```bash
   TIKTOK_CLIENT_KEY=...
   TIKTOK_CLIENT_SECRET=...
   TIKTOK_REDIRECT_URI=https://n8n.etsrv.site/tiktok/callback
   ```
3. **https://n8n.etsrv.site/tiktok/** → Autorizar

Publisher real pendiente hasta aprobación TikTok.

---

## Servicios systemd

```bash
sudo cp deploy/systemd/easytech-{meta,google,tiktok}-oauth.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now easytech-meta-oauth easytech-google-oauth easytech-tiktok-oauth
```

## Cron (usuario papichulo)

Ver `deploy/crontab.example` — incluye Meta Mié/Vie y Google Sáb.

## API Accio

```bash
# Meta
curl -X POST https://n8n.etsrv.site/accio/run/publish-meta \
  -H "Authorization: Bearer $ACCIO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"platform":"all","force":false}'

# Google Business
curl -X POST https://n8n.etsrv.site/accio/run/publish-channel \
  -H "Authorization: Bearer $ACCIO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"connector":"google_business","force":false}'
```

## Requisito común: flyers públicos

Meta e Instagram necesitan URL pública del PNG:
`https://n8n.etsrv.site/accio/assets/flyers/NOMBRE.png`

El cron ejecuta `validate_flyers.py` antes de publicar.
