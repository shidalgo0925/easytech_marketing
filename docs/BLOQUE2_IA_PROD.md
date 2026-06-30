# Bloque 2 — IA en producción

**Objetivo:** LiteLLM/CODITO operativo · enrich real (no `llm_skipped`) en pipeline, campañas y contenido.

---

## Estado

| Item | Estado |
|------|--------|
| AI Provider Manager (`ai_provider/`) | ✅ código |
| Marketing Brain enrich | ✅ código |
| Variables prod | ⏳ requiere `ACCIO_AI_BASE_URL` |
| Red ARROZCONPOLLO → CODITO | ⏳ **bloqueante ops** |

**Cierre Bloque 2** = `verify_marketing_ai_prod.py` exit 0 + pipeline con enrich real.

---

## Activación (1 comando)

```bash
CODITO_HOST=<IP_CODITO> ./scripts/enable_ai_prod.sh
```

Valida LiteLLM, escribe `.env`, reinicia servicio.

---

## Verificación

```bash
./venv/bin/python3 scripts/validate_codito_ai.py
./venv/bin/python3 scripts/verify_marketing_ai_prod.py
```

---

## Conectividad

Ver [CONECTAR_CODITO.md](CONECTAR_CODITO.md) — IP directa, túnel SSH o `/etc/hosts`.

---

## Diagnóstico actual (ARROZCONPOLLO)

- `codito.etsrv.site` → **NXDOMAIN**
- Puertos 4000 locales → sin LiteLLM
- Sin `ACCIO_AI_BASE_URL` en `.env`

**Acción requerida:** proporcionar IP/hostname de CODITO o abrir túnel.

---

## Siguiente bloque

**Bloque 3** — Ejecución comercial completa (LinkedIn real, Meta, EN1).
