#!/usr/bin/env python3
"""Cliente OpenAI para el Asistente EM+Acción (chat conversacional + tools)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from Motor_Tecnico.accio_engine import tenant_secrets

DEFAULT_MODEL = "gpt-4o-mini"


def resolve_model(tenant_id: str, ai_cfg: dict[str, Any] | None = None) -> str:
    env_model = os.getenv("OPENAI_MODEL", "").strip()
    if env_model:
        return env_model
    cfg = ai_cfg or {}
    return (cfg.get("openai_model") or DEFAULT_MODEL).strip() or DEFAULT_MODEL


def assistant_enabled(ai_cfg: dict[str, Any] | None = None) -> bool:
    raw = os.getenv("AI_ASSISTANT_ENABLED", "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    cfg = ai_cfg or {}
    return cfg.get("enabled", True) is not False

ACTION_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "create_post_drafts",
            "description": (
                "Prepara borradores de publicación para revisión del usuario. "
                "NO publica en redes. El usuario debe aprobar en el panel «Borradores pendientes»."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "app_id": {"type": "string", "description": "App de marketing (en1, eposone, default, odoo-fe, etc.)"},
                    "count": {"type": "integer", "description": "Cantidad de publicaciones (1-10)"},
                    "platform": {
                        "type": "string",
                        "enum": ["linkedin", "facebook", "instagram", "tiktok", "youtube", "google_business"],
                    },
                    "topic": {"type": "string", "description": "Tema o ángulo del contenido"},
                    "content_type": {
                        "type": "string",
                        "enum": ["educacion", "consejo", "venta", "caso", "tendencia"],
                    },
                },
                "required": ["count", "platform", "topic"],
            },
        },
    },
]


def resolve_openai_key(tenant_id: str) -> str:
    key = tenant_secrets.get_secret(tenant_id, "variables", "openai_api_key")
    if key:
        return key.strip()
    return os.getenv("OPENAI_API_KEY", "").strip()


def llm_available(tenant_id: str, ai_cfg: dict[str, Any] | None = None) -> bool:
    if not assistant_enabled(ai_cfg):
        return False
    return bool(resolve_openai_key(tenant_id))


def compact_context(ctx: dict[str, Any]) -> dict[str, Any]:
    """Contexto resumido para el prompt (límite de tokens)."""
    bc = ctx.get("business_context") or {}
    posts = ctx.get("queue_posts") or []
    published = ctx.get("published_recent") or []
    sel = ctx.get("selected_post")
    return {
        "tenant_id": ctx.get("tenant_id"),
        "app_id": ctx.get("app_id"),
        "view": ctx.get("view"),
        "empresa": bc.get("nombre_empresa") or bc.get("display_name"),
        "productos": (bc.get("productos_servicios") or [])[:12],
        "cta": bc.get("cta_principal"),
        "tono": bc.get("tono_comunicacion") or (ctx.get("ai_config") or {}).get("tone_override"),
        "cola_pendiente": ctx.get("queue_pending"),
        "cola_resumen": [
            {
                "id": p.get("id"),
                "platform": p.get("platform"),
                "status": p.get("status"),
                "scheduled_at": p.get("scheduled_at"),
                "preview": (p.get("text") or "")[:160],
            }
            for p in posts[:12]
        ],
        "publicadas_recientes": [
            {"id": p.get("id"), "platform": p.get("platform"), "published_at": p.get("published_at")}
            for p in published[:8]
        ],
        "estados": ctx.get("status_counts"),
        "publicacion_seleccionada": (
            {
                "id": sel.get("id"),
                "platform": sel.get("platform"),
                "status": sel.get("status"),
                "text": (sel.get("text") or "")[:500],
            }
            if sel
            else None
        ),
        "articulos_kb": [
            {"slug": a.get("slug"), "title": a.get("title")}
            for a in (ctx.get("knowledge_summary") or {}).get("articles", [])[:15]
        ],
        "auto_publish": (ctx.get("publication_settings") or {}).get("auto_publish", False),
        "productos_catalogo": [
            {"slug": p.get("slug"), "name": p.get("name"), "cta": p.get("cta")}
            for p in (ctx.get("products") or [])[:15]
        ],
        "campanas_activas": [
            {
                "id": c.get("id"),
                "product": c.get("product"),
                "channel": c.get("channel"),
                "status": c.get("status"),
                "scheduled_at": c.get("scheduled_at"),
            }
            for c in (ctx.get("campaigns") or [])[:15]
        ],
        "conectores": ctx.get("connectors") or [],
        "apps_catalogo": [
            {
                "app_id": a.get("app_id"),
                "name": a.get("name"),
                "selected": a.get("selected_now"),
                "tone": a.get("tone"),
                "target_audience": (a.get("target_audience") or "")[:120],
                "description": (a.get("description") or "")[:160],
                "product_slug_kb": a.get("product_slug_kb"),
                "knowledge_topics": a.get("knowledge_topics") or [],
                "posts_total": (a.get("stats") or {}).get("posts_total", 0),
                "pendientes": (a.get("stats") or {}).get("pending_publishable", 0),
                "publicadas": (a.get("stats") or {}).get("published", 0),
                "campanas": (a.get("stats") or {}).get("campaigns_total", 0),
                "by_status": (a.get("stats") or {}).get("by_status") or {},
            }
            for a in (ctx.get("apps_catalog") or [])
        ],
        "app_activa": ctx.get("active_app"),
    }


def build_system_prompt(ctx: dict[str, Any], pending_orders: int) -> str:
    tone = (ctx.get("ai_config") or {}).get("tone_override") or ""
    tone_line = f"Tono de marca: {tone}." if tone else "Tono: profesional, cercano, B2B Panamá/LATAM."
    return f"""Eres el Asistente EM+Acción, copiloto de marketing dentro de la plataforma EM+Acción.

Responde SIEMPRE en español, de forma natural y conversacional — como ChatGPT, pero enfocado en marketing.

Reglas:
- Conoces el tenant, TODAS las apps del tenant (apps_catalogo), la app activa (app_activa), cola, publicaciones, knowledge base y métricas del contexto JSON.
- Si el usuario menciona un producto (EN1, ePOSOne, EPayRoll, Odoo FE, etc.), usa el app_id correcto del catálogo al crear borradores.
- NUNCA publicas en redes sin aprobación explícita del usuario.
- Si el usuario pide crear publicaciones, usa la herramienta create_post_drafts y explícale que el borrador aparece abajo en «Borradores pendientes» → Aprobar → cola → pestaña Publicaciones.
- Si pregunta dónde ver algo, indica pasos concretos en la UI (Publicaciones, Campañas, panel del asistente).
- Puedes opinar, estrategia, ideas, reescrituras en el chat; para encolar contenido usa la herramienta.
- {tone_line}
- Borradores pendientes de aprobación ahora: {pending_orders}.

Contexto operativo:
{json.dumps(compact_context(ctx), ensure_ascii=False, indent=2)}
"""


def _api_request(body: dict[str, Any], api_key: str) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def estimate_cost(usage: dict[str, Any]) -> float | None:
    if not usage:
        return None
    return round(
        usage.get("prompt_tokens", 0) * 0.00000015 + usage.get("completion_tokens", 0) * 0.0000006,
        4,
    )


def chat_completion(
    tenant_id: str,
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    ai_cfg: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
    temperature: float = 0.65,
) -> tuple[dict[str, Any], str, float | None]:
    """Returns (message_dict, model_name, cost). message may include tool_calls."""
    api_key = resolve_openai_key(tenant_id)
    if not api_key:
        raise RuntimeError("OPENAI_KEY_MISSING")

    model_name = model or resolve_model(tenant_id, ai_cfg)
    body: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    try:
        data = _api_request(body, api_key)
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")[:400]
        raise RuntimeError(f"OpenAI HTTP {exc.code}: {err_body}") from exc

    msg = data["choices"][0]["message"]
    return msg, model_name, estimate_cost(data.get("usage", {}))


def audit_to_messages(tenant_id: str, limit: int = 8) -> list[dict[str, str]]:
    from Motor_Tecnico.accio_engine import assistant_store

    items = assistant_store.list_audit(tenant_id, limit=limit)
    items = list(reversed(items))  # cronológico
    out: list[dict[str, str]] = []
    for row in items:
        if row.get("prompt"):
            out.append({"role": "user", "content": row["prompt"]})
        if row.get("response"):
            out.append({"role": "assistant", "content": row["response"]})
    return out[-limit * 2 :]


def normalize_client_history(history: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    if not history:
        return []
    out: list[dict[str, str]] = []
    for row in history[-12:]:
        role = row.get("role")
        text = (row.get("content") or row.get("text") or "").strip()
        if role in ("user", "assistant") and text:
            out.append({"role": role, "content": text})
    return out
