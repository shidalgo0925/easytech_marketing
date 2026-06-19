# Meta — Facebook + Instagram (Fase D.2 / D.3)

Publicación automática desde `Marketing/content_queue.json` vía Graph API v21.0.

## Requisitos

1. **App Meta** en [developers.facebook.com](https://developers.facebook.com/apps/)
2. **Página de Facebook** EasyTech Services
3. **Instagram Business** vinculada a esa página
4. Productos / permisos: Facebook Login, Pages API, Instagram Graph API

## Variables `.env`

```bash
META_APP_ID=tu_app_id
META_APP_SECRET=tu_app_secret
META_REDIRECT_URI=https://n8n.etsrv.site/meta/callback
META_PAGE_ID=          # opcional; se detecta en OAuth
META_PAGE_ACCESS_TOKEN=
META_IG_USER_ID=
META_USER_ACCESS_TOKEN=
PUBLIC_SITE_URL=https://n8n.etsrv.site
META_OAUTH_PORT=8093
```

## OAuth (una vez)

1. En la app Meta → Facebook Login → Valid OAuth Redirect URIs:  
   `https://n8n.etsrv.site/meta/callback`
2. Abrir: **https://n8n.etsrv.site/meta/**
3. Autorizar → tokens guardados en `.env`

## Publicar

```bash
# Dry-run
python3 Motor_Tecnico/meta_publisher.py --platform=facebook --dry-run
python3 Motor_Tecnico/meta_publisher.py --platform=instagram --dry-run

# Siguiente post listo (respeta fecha)
python3 Motor_Tecnico/meta_publisher.py --platform=facebook
python3 Motor_Tecnico/meta_publisher.py --platform=instagram

# Forzar ahora
python3 Motor_Tecnico/meta_publisher.py --platform=facebook --force
```

Dashboard: botón **Meta** o pestaña **Conectores**.

API:

```bash
curl -X POST https://n8n.etsrv.site/accio/run/publish-meta \
  -H "Authorization: Bearer $ACCIO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"platform":"all","force":false}'
```

## Cola

Posts con `"platform": "facebook"` o `"instagram"` en `content_queue.json`.

Flyers deben ser accesibles públicamente en:  
`https://n8n.etsrv.site/accio/assets/flyers/NOMBRE.png`

Log: `Marketing/meta_publish_log.json`

## Cron (opcional)

Ver `deploy/crontab.example` — Mié/Vie después de LinkedIn.

## systemd

```bash
sudo cp deploy/systemd/easytech-meta-oauth.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now easytech-meta-oauth
```

## nginx

```nginx
location /meta/ {
    proxy_pass http://127.0.0.1:8093/meta/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```
