# Accio AI Provider Manager

**Estado:** V1 en implementación · **Proveedor inicial:** LiteLLM en CODITO → Ollama

## Arquitectura

```
EM+Acción (ARROZCONPOLLO)
        ↓
Accio AI Provider Manager   Motor_Tecnico/accio_engine/ai_provider/
        ↓
LiteLLM (CODITO)
        ↓
Ollama (qwen2.5-coder:14b o 7b)
```

EM+Acción **no** llama a `api.openai.com` ni pide `OPENAI_API_KEY` en UI.

## Variables de entorno (servidor)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `ACCIO_AI_PROVIDER` | `litellm` | Proveedor V1 |
| `ACCIO_AI_BASE_URL` | — | URL base LiteLLM (sin `/v1`) |
| `ACCIO_AI_MODEL` | `qwen2.5-coder:14b` | Modelo Ollama vía LiteLLM |
| `ACCIO_AI_API_KEY` | — | Solo si LiteLLM exige Bearer |
| `ACCIO_AI_TIMEOUT` | `90` | Timeout HTTP segundos |
| `AI_ASSISTANT_ENABLED` | — | `true` / `false` global |

Alias: `LITELLM_BASE_URL`, `LITELLM_API_KEY`, `AI_MODEL`.

## Validación

```bash
python3 scripts/validate_codito_ai.py
```

## API status

`GET /accio/{tenant}/assistant/status` expone:

- `llm_available`
- `provider`, `provider_configured`, `provider_reachable`
- `model`

`has_openai_key` queda deprecated (siempre `false`).

## Código

| Módulo | Rol |
|--------|-----|
| `ai_provider/config.py` | Env |
| `ai_provider/litellm.py` | Cliente HTTP OpenAI-compatible |
| `ai_provider/manager.py` | `chat_completion`, `llm_available`, `provider_status` |
| `assistant_llm.py` | Fachada asistente (tools, prompts) |

**Roadmap sprint:** [ROADMAP.md](ROADMAP.md) § Próximo sprint — Accio AI Provider Manager.
