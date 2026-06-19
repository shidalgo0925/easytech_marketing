# Instalación — EasyMarketingOne

## Requisitos

- Ubuntu 22.04+ / Debian
- Python 3.12, Docker, nginx, certbot
- Dominio con SSL (ej. `n8n.etsrv.site`)

## 1. Clonar e instalar

```bash
sudo mkdir -p /opt/easytech_marketing
sudo chown $USER:$USER /opt/easytech_marketing
git clone https://github.com/TU_ORG/EasyMarketingOne.git /opt/easytech_marketing
cd /opt/easytech_marketing

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Secretos

```bash
cp .env.example .env
nano .env   # ver deploy/SECRETS.md
chmod 600 .env
```

Generar API key:

```bash
openssl rand -hex 24
```

## 3. systemd

```bash
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now easytech-lead-api easytech-linkedin-oauth easytech-accio-engine
```

## 4. Docker n8n

```bash
docker compose up -d
```

## 5. nginx

Proxy en `n8n.etsrv.site`:

- `/` → n8n `:5678`
- `/accio/` → accio engine `:8092`
- `/guia/` → `/var/www/guia/`
- `/guia/api/` → lead API `:8080`
- `/linkedin/` → oauth `:8091`

## 6. Cron

```bash
crontab -e
# Pegar contenido de deploy/crontab.example
```

## 7. Verificar

```bash
curl http://127.0.0.1:8092/accio/health
curl -H "Authorization: Bearer $ACCIO_API_KEY" http://127.0.0.1:8092/accio/status
```

Dashboard: `https://TU_DOMINIO/accio/dashboard/`

## Landing guía

Copiar HTML a `/var/www/guia/` (no incluido en repo — desplegar aparte).
