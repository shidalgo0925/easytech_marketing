# Bloque 1 — Cimentación prod (Fases A + B)

**Objetivo:** `marketing_os.db` como fuente de verdad en prod con stores `dual` y backup operativo.

**Estado:** ✅ cerrado cuando `verify_marketing_os_prod.py` pasa en el VPS.

---

## Qué incluye

1. **BD plataforma** — `Marketing/platform/marketing_os.db` (schema v1–v16)
2. **Migraciones M1–M9** — JSON legacy → SQLite
3. **Stores dual** — lectura SQL primero, fallback JSON; escritura en ambos
4. **`deploy/secrets/.env.prod`** — config estructural prod (sin API keys)
5. **Backup** — `backup_marketing_os_db.sh` + `backup_secrets.sh`

---

## Variables prod

```env
ACCIO_PLATFORM_DB=/opt/easytech_marketing/Marketing/platform/marketing_os.db
ACCIO_MEMORY_STORE=sql
ACCIO_BRAIN_STORE=dual
ACCIO_BRAND_STORE=dual
ACCIO_PUBLICATION_STORE=dual
ACCIO_PRODUCT_STORE=dual
ACCIO_KNOWLEDGE_STORE=dual
ACCIO_CAMPAIGN_STORE=dual
ACCIO_ASSET_STORE=dual
ACCIO_LEAD_STORE=dual
```

Secretos (`ACCIO_API_KEY`, Odoo, LinkedIn…) permanecen en `.env` raíz (systemd carga `.env.prod` luego `.env`).

---

## Comandos

```bash
# Backup antes de migrar
./scripts/backup_marketing_os_db.sh

# Migrar (dry-run primero)
./scripts/run_marketing_os_migrations.sh --dry-run
./scripts/run_marketing_os_migrations.sh

# Verificar Bloque 1
./scripts/verify_marketing_os_prod.py

# Reiniciar
sudo systemctl restart easytech-accio-engine
```

---

## Rollback

```bash
cp ~/backups/emaccion/marketing_os-latest.db Marketing/platform/marketing_os.db
sudo systemctl restart easytech-accio-engine
```

Cambiar stores a `json` solo en emergencia (pierde datos solo en SQL).

---

## Criterios de cierre

- [ ] `marketing_os.db` con datos M1–M9
- [ ] `ACCIO_*_STORE` en prod
- [ ] `deploy/secrets/.env.prod` presente
- [ ] Backup BD probado
- [ ] `verify_marketing_os_prod.py` OK
- [ ] Servicio estable tras restart

---

## Siguiente bloque

**Bloque 2** — IA en producción (CODITO/LiteLLM + enrich real).
