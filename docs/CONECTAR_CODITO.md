# Conectar CODITO — LiteLLM → EM+Acción

**CODITO** es el servidor con Open WebUI + LiteLLM + Ollama (`qwen2.5-coder`).

**ARROZCONPOLLO** (`95.111.244.137`) debe poder alcanzar LiteLLM en el puerto **4000** (típico).

---

## Diagnóstico rápido

```bash
./venv/bin/python3 scripts/validate_codito_ai.py
./venv/bin/python3 scripts/verify_marketing_ai_prod.py
```

Si `ACCIO_AI_BASE_URL` está vacío o `codito.etsrv.site` no resuelve → IA en modo degradado (`llm_skipped=true`).

---

## Opción A — IP directa (recomendada)

1. Obtener IP/hostname de CODITO en la red (VPN, LAN, etc.).
2. Probar desde ARROZCONPOLLO:
   ```bash
   curl -s --connect-timeout 3 http://<CODITO_IP>:4000/v1/models | head
   ```
3. Activar:
   ```bash
   CODITO_HOST=<CODITO_IP> CODITO_PORT=4000 ./scripts/enable_ai_prod.sh
   ```

---

## Opción B — Túnel SSH

Si CODITO solo es accesible por SSH:

```bash
CODITO_SSH=usuario@codito ./scripts/codito_ssh_tunnel.sh
# En otra terminal / .env:
# ACCIO_AI_BASE_URL=http://127.0.0.1:14000
```

---

## Opción C — /etc/hosts

Si existe DNS interno `codito.etsrv.site`:

```bash
echo "<CODITO_IP> codito.etsrv.site" | sudo tee -a /etc/hosts
CODITO_HOST=codito.etsrv.site ./scripts/enable_ai_prod.sh
```

---

## Variables

| Variable | Valor |
|----------|-------|
| `ACCIO_AI_PROVIDER` | `litellm` |
| `ACCIO_AI_BASE_URL` | `http://<host>:4000` |
| `ACCIO_AI_MODEL` | `qwen2.5-coder:7b` o `qwen2.5-coder:14b` |
| `ACCIO_AI_ENABLED` | `true` |

---

## Fallback OpenAI (solo emergencia)

```env
ACCIO_AI_PROVIDER=litellm
ACCIO_AI_OPENAI_FALLBACK=true
OPENAI_API_KEY=sk-...
```

No es el camino V1 del plan (CODITO primero).

---

## Verificar enrich en pipeline

Tras activar IA:

1. `sudo systemctl restart easytech-accio-engine`
2. `/accio/plan/easytech/` → **Pipeline completo**
3. Respuesta debe incluir `llm_enriched > 0` o enrich sin `llm_skipped`
