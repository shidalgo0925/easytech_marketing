# Fase A V2 — Checklist de cierre

**Referencia:** [EMACCION_V2_PLAN_MAESTRO.md](../EMACCION_V2_PLAN_MAESTRO.md) §4

---

## Infraestructura

- [x] systemd servicios PROD (`easytech-accio-engine`, OAuth, lead-api)
- [x] nginx proxy `/accio/` en `n8n.etsrv.site`
- [x] nginx vhost `emaccion.etsrv.site` (HTTP origen + Cloudflare HTTPS)
- [x] Modelo DEV / TEST / PROD documentado
- [x] `env_loader.py` + `ACCIO_ENV` en health
- [x] systemd units dev/test (opcionales)
- [ ] SSL origen Let's Encrypt `emaccion.etsrv.site` (opcional si CF Full)
- [ ] `deploy/secrets/.env.prod` poblado en VPS (manual, fuera de Git)

## Secretos y backup

- [x] Script `scripts/backup_secrets.sh` (tar + gpg)
- [x] `deploy/SECRETS.md` actualizado vía DEV_TEST_PROD
- [ ] Primera ejecución backup con `BACKUP_GPG_PASSPHRASE`
- [x] Secretos tenant en SQLite cifrado (Fase C parcial)

## Repositorio y docs

- [x] Git + README
- [x] Plan V2 + roadmap + estado
- [x] `docs/INSTALACION.md` (pendiente link DEV_TEST_PROD)
- [ ] Repo sin archivos huérfanos (revisión manual)

## Logs

- [x] `logs/` en VPS
- [ ] Rotación logrotate (opcional)

## Pruebas de cierre

```bash
curl -s http://127.0.0.1:8092/accio/health | jq .env   # → "prod"
python3 -m unittest tests/test_tenant_isolation.py -v
```

## Evidencia

| Fecha | Resultado |
|-------|-----------|
| 2026-06-26 | health env=prod, tests tenant OK |

**Estado:** 🔄 ~90% — falta backup ejecutado + `.env.prod` en deploy/secrets en VPS.
