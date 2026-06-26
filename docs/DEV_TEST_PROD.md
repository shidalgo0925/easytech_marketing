# DEV · TEST · PROD — EM+Acción V2

**Fase A** — entornos independientes sin mezclar configuración.

---

## Modelo

| Entorno | Variable | Puerto default | Uso |
|---------|----------|----------------|-----|
| **PROD** | `ACCIO_ENV=prod` | 8092 | VPS en vivo, `emaccion.etsrv.site` |
| **DEV** | `ACCIO_ENV=dev` | 8192 | Desarrollo local / sandbox |
| **TEST** | `ACCIO_ENV=test` | 8193 | CI e integración |

---

## Archivos de secretos (gitignored)

```
deploy/secrets/.env.prod
deploy/secrets/.env.dev
deploy/secrets/.env.test
```

Plantillas: `deploy/environments/.env.{prod,dev,test}.example`

**Setup inicial PROD:**

```bash
cp deploy/environments/.env.prod.example deploy/secrets/.env.prod
# Copiar valores reales desde .env existente
nano deploy/secrets/.env.prod
chmod 600 deploy/secrets/.env.prod
```

---

## systemd

| Servicio | Entorno |
|----------|---------|
| `easytech-accio-engine` | PROD |
| `easytech-accio-engine-dev` | DEV (no auto-enable) |
| `easytech-accio-engine-test` | TEST (no auto-enable) |

```bash
sudo cp deploy/systemd/easytech-accio-engine*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart easytech-accio-engine
```

---

## Carga en la app

`Motor_Tecnico/accio_engine/env_loader.py` busca en orden:

1. `deploy/secrets/.env.{ACCIO_ENV}`
2. `.env.{ACCIO_ENV}`
3. `.env`

`/accio/health` devuelve `"env": "prod"|"dev"|"test"`.

---

## Backup cifrado

```bash
BACKUP_GPG_PASSPHRASE='tu-frase-segura' ./scripts/backup_secrets.sh
```

Respalda `.env`, `deploy/secrets/.env.*` y `Marketing/tenants/.secrets/`.

---

## Regla

**Nunca** usar credenciales PROD en DEV/TEST. **Nunca** commitear `deploy/secrets/`.
