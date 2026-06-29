#!/usr/bin/env python3
"""Asistente EM+Acción — contexto, órdenes y chat operativo."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from Motor_Tecnico.accio_engine import assistant_store, dashboard_data, executor, knowledge_api, marketing_app, publications_api
from Motor_Tecnico.accio_engine import settings_center, tenant_secrets
from Motor_Tecnico.accio_engine.editorial import editorial_label, is_publishable, normalize_status
from Motor_Tecnico.accio_engine.tenant import DEFAULT_TENANT

PANAMA = ZoneInfo("America/Panama")

APP_ALIASES: dict[str, str] = {
    "en1": "en1",
    "easynodeone": "en1",
    "epayroll": "epayroll",
    "eposone": "eposone",
    "eclassone": "eclassone",
    "ethesisone": "ethesisone",
    "odoo": "odoo-fe",
    "fe": "odoo-fe",
    "facturacion": "odoo-fe",
    "consultoria": "consultoria",
    "desarrollo": "desarrollo",
    "emaccion": "default",
    "em+accion": "default",
    "em accion": "default",
    "em+acción": "default",
}

PRODUCT_SLUG_BY_APP: dict[str, str] = {
    "default": "easytech",
    "en1": "en1",
    "epayroll": "epayroll",
    "eposone": "eposone",
    "eclassone": "eclassone",
    "ethesisone": "ethesisone",
    "odoo-fe": "odoo_fe",
    "consultoria": "casos_exito",
    "desarrollo": "easytech",
}


def _connectors_summary(tenant_id: str) -> list[dict[str, Any]]:
    view = tenant_secrets.get_settings_view(tenant_id)
    out: list[dict[str, Any]] = []
    for conn_id, fields in (view.get("connectors") or {}).items():
        configured = any(f.get("configured") for f in fields)
        active = any(f.get("validation_status") == "active" for f in fields)
        out.append({"id": conn_id, "configured": configured, "active": active})
    return out


def _read_json_file(path: Path | None) -> dict[str, Any]:
    if not path or not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _app_knowledge_topics(tenant_id: str, app_id: str) -> list[str]:
    paths = marketing_app.effective_app_paths(tenant_id, app_id)
    kdir = paths.get("knowledge_dir")
    if not kdir or not kdir.is_dir():
        return []
    topics: list[str] = []
    for md in sorted(kdir.glob("*.md"))[:5]:
        try:
            line = md.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        except OSError:
            line = md.stem
        topics.append(line or md.stem)
    return topics


def _app_queue_stats(tenant_id: str, app_id: str) -> dict[str, Any]:
    queue = executor.load_content_queue_for_app(tenant_id, app_id)
    posts = queue.get("posts", [])
    by_status: dict[str, int] = {}
    for post in posts:
        st = normalize_status(post.get("status"))
        by_status[st] = by_status.get(st, 0) + 1
    pending = [p for p in posts if is_publishable(p.get("status"))]
    next_scheduled = None
    schedulable = [p for p in posts if p.get("scheduled_at")]
    if schedulable:
        next_scheduled = sorted(schedulable, key=lambda x: x.get("scheduled_at") or "")[0].get("scheduled_at")
    campaigns = dashboard_data.load_campaigns(tenant_id, app_id)
    published = sum(1 for p in posts if normalize_status(p.get("status")) == "published")
    return {
        "posts_total": len(posts),
        "pending_publishable": len(pending),
        "published": published,
        "by_status": by_status,
        "next_scheduled_at": next_scheduled,
        "campaigns_total": len(campaigns),
    }


def build_apps_catalog(tenant_id: str, active_app_id: str) -> list[dict[str, Any]]:
    """Catálogo completo de apps del tenant para contexto del asistente."""
    catalog: list[dict[str, Any]] = []
    for app in marketing_app.list_apps(tenant_id):
        paths = marketing_app.effective_app_paths(tenant_id, app.app_id)
        profile = _read_json_file(paths.get("profile"))
        branding = _read_json_file(paths.get("branding"))
        stats = _app_queue_stats(tenant_id, app.app_id)
        product_slug = PRODUCT_SLUG_BY_APP.get(app.app_id, "easytech" if app.app_id == "default" else app.app_id)
        catalog.append(
            {
                "app_id": app.app_id,
                "name": app.name,
                "slug": app.slug,
                "is_default": app.is_default,
                "selected_now": app.app_id == active_app_id,
                "status": app.status,
                "description": profile.get("description") or app.description,
                "tone": profile.get("tone") or app.tone,
                "target_audience": profile.get("target_audience") or app.target_audience,
                "product_slug_kb": product_slug,
                "logo_url": branding.get("logo_url") or app.logo_url,
                "brand_colors": branding.get("brand_colors") or app.brand_colors or {},
                "knowledge_topics": _app_knowledge_topics(tenant_id, app.app_id),
                "stats": stats,
            }
        )
    return catalog


def build_context(
    tenant_id: str,
    app_id: str | None = None,
    *,
    view: str = "",
    selected_post_id: str | None = None,
) -> dict[str, Any]:
    aid = marketing_app.normalize_app_id(app_id or marketing_app.default_app_id(tenant_id))
    queue = executor.load_content_queue_for_app(tenant_id, aid)
    pubs = publications_api.list_publications(tenant_id, app_id=aid, limit=30)
    published = [p for p in pubs["publications"] if p["status"] == "published"][:10]
    pending = [p for p in queue.get("posts", []) if is_publishable(p.get("status"))]
    products = settings_center.load_products(tenant_id).get("products", [])
    campaigns = dashboard_data.load_campaigns(tenant_id, aid)
    apps_catalog = build_apps_catalog(tenant_id, aid)
    active_app = next((a for a in apps_catalog if a.get("selected_now")), None)
    return {
        "tenant_id": tenant_id,
        "app_id": aid,
        "view": view,
        "apps_catalog": apps_catalog,
        "active_app": active_app,
        "business_context": knowledge_api.load_business_context(tenant_id),
        "editorial_rules": knowledge_api.load_editorial_rules(tenant_id),
        "knowledge_summary": knowledge_api.knowledge_summary(tenant_id),
        "products": products,
        "campaigns": campaigns,
        "connectors": _connectors_summary(tenant_id),
        "queue_pending": len(pending),
        "queue_posts": queue.get("posts", [])[:20],
        "published_recent": published,
        "calendar": executor.load_content_queue_for_app(tenant_id, aid),
        "publication_settings": settings_center.load_publication(tenant_id),
        "ai_config": settings_center.load_ai_config(tenant_id),
        "selected_post": publications_api.find_publication(tenant_id, selected_post_id, aid) if selected_post_id else None,
        "status_counts": pubs.get("status_counts", {}),
    }


def _resolve_app_from_text(text: str, default_app: str) -> str:
    lower = text.lower()
    for alias, app_id in APP_ALIASES.items():
        if alias in lower:
            return app_id
    return default_app


def _resolve_platform(text: str, default: str = "linkedin") -> str:
    lower = text.lower()
    for p in ("linkedin", "facebook", "instagram", "tiktok", "youtube", "google_business"):
        if p.replace("_", " ") in lower or p in lower:
            return p
    return default


def _extract_count(text: str, default: int = 1) -> int:
    m = re.search(r"\b(\d{1,2})\b", text)
    if m:
        return max(1, min(int(m.group(1)), 20))
    if "cinco" in text.lower() or " 5 " in f" {text.lower()} ":
        return 5
    if "diez" in text.lower() or " 10 " in f" {text.lower()} ":
        return 10
    return default


def _product_slug(app_id: str) -> str:
    return PRODUCT_SLUG_BY_APP.get(app_id, "easytech")


def _generate_posts_preview(
    tenant_id: str,
    app_id: str,
    count: int,
    platform: str,
    topic_hint: str = "",
) -> list[dict[str, Any]]:
    previews = []
    slug = _product_slug(app_id)
    types = ["educacion", "consejo", "venta", "educacion", "caso"]
    for i in range(count):
        ct = types[i % len(types)]
        topic = topic_hint or f"Tema {i + 1} — {app_id}"
        if count > 1:
            topic = f"{topic_hint or app_id} ({i + 1}/{count})"
        gen = knowledge_api.generate_topic(
            topic=topic,
            product_slug=slug,
            content_type=ct,
            platform=platform,
            tenant_id=tenant_id,
        )
        post = gen["post"]
        post["app_id"] = app_id
        post["status"] = "pending_approval"
        previews.append(post)
    return previews


def _analyze_queue(ctx: dict[str, Any]) -> str:
    posts = ctx.get("queue_posts") or []
    if not posts:
        return "La cola está vacía para esta App. Recomiendo generar 3–5 borradores educativos antes de contenido de venta."
    weak = []
    strong = []
    for p in posts:
        st = normalize_status(p.get("status"))
        text_len = len(p.get("text") or "")
        if st in ("draft", "failed") or text_len < 120:
            weak.append(p.get("id"))
        elif is_publishable(st):
            strong.append(p.get("id"))
    lines = [f"Cola: {len(posts)} publicaciones · {len(strong)} listas · {len(weak)} débiles."]
    if weak:
        lines.append(f"Revisar: {', '.join(weak[:5])}.")
    balance = knowledge_api.editorial_balance(posts, ctx["tenant_id"])
    lines.append(
        f"Balance editorial pendiente: {balance['current']['valor_pct']}% valor / {balance['current']['venta_pct']}% venta."
    )
    return " ".join(lines)


def _summarize_month(ctx: dict[str, Any]) -> str:
    published = ctx.get("published_recent") or []
    if not published:
        return "No hay publicaciones recientes en esta App. Sugiero retomar con 2 posts de valor y 1 de venta."
    by_platform: dict[str, int] = {}
    for p in published:
        plat = p.get("platform") or "?"
        by_platform[plat] = by_platform.get(plat, 0) + 1
    parts = [f"{k}: {v}" for k, v in sorted(by_platform.items())]
    return f"Resumen reciente ({len(published)} posts): " + ", ".join(parts) + "."


def _where_to_see_posts(tenant_id: str, app_id: str) -> str:
    pending = assistant_store.list_pending_orders(tenant_id)
    n = len(pending)
    lines = [
        "Los borradores que preparo aparecen en este mismo panel, entre el chat y el cuadro de texto:",
        "busca la sección «Borradores pendientes» con los botones Aprobar y Rechazar.",
        "",
        "Después de aprobar, la publicación queda en:",
        "• Pestaña Publicaciones (filtro Pend. aprobación o Programado)",
        "• Pestaña Campañas o Resumen → Cola de publicaciones",
        "",
    ]
    if n:
        lines.append(f"Ahora tienes {n} borrador(es) esperando aprobación aquí abajo.")
        for o in pending[:3]:
            prev = (o.get("preview") or [{}])[0]
            lines.append(f"  → {o.get('title')} (ID: {prev.get('id', '—')})")
    else:
        lines.append("No veo borradores pendientes ahora. Si acabas de pedir uno, recarga la página o repite «Crea 1 publicación».")
    return "\n".join(lines)


def _emaccion_marketing_advice() -> str:
    return (
        "Para promocionar EM+Acción (la plataforma) en LinkedIn te sugiero este enfoque:\n\n"
        "1. Valor: «Centro de mando de marketing — cola, campañas, IA y métricas en un solo lugar».\n"
        "2. Dolor: equipos que publican en Excel/WhatsApp sin historial ni medición.\n"
        "3. CTA: demo o diagnóstico (no vender features sueltos).\n"
        "4. Tono: ejecutivo, claro, Panamá/LATAM.\n\n"
        "Si quieres que genere el borrador ya, dime: «Genera 1 publicación de EM+Acción para LinkedIn».\n"
        "Lo verás abajo en «Borradores pendientes» → Aprobar → pestaña Publicaciones."
    )


def _call_openai(prompt: str, system: str, tenant_id: str, ai_cfg: dict[str, Any] | None = None) -> tuple[str, str, float | None]:
    from Motor_Tecnico.accio_engine import assistant_llm

    api_key = assistant_llm.resolve_openai_key(tenant_id)
    if not api_key:
        return "", "rules", None
    model = assistant_llm.resolve_model(tenant_id, ai_cfg)
    try:
        import urllib.request

        body = json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"].strip()
        usage = data.get("usage", {})
        cost = round((usage.get("prompt_tokens", 0) * 0.00000015 + usage.get("completion_tokens", 0) * 0.0000006), 4)
        return text, model, cost
    except Exception:
        return "", "rules", None


def _execute_tool_call(
    name: str,
    args: dict[str, Any],
    tenant_id: str,
    default_app: str,
    user: str,
    prompt: str,
) -> tuple[list[dict[str, Any]], str]:
    """Ejecuta tool LLM; retorna (orders, result_text_for_tool)."""
    orders: list[dict[str, Any]] = []
    if name == "create_post_drafts":
        app_id = marketing_app.normalize_app_id(args.get("app_id") or default_app)
        count = max(1, min(int(args.get("count") or 1), 10))
        platform = str(args.get("platform") or "linkedin").lower()
        topic = str(args.get("topic") or "Tema marketing")
        ct = str(args.get("content_type") or "educacion")
        previews = _generate_posts_preview(tenant_id, app_id, count, platform, topic_hint=topic)
        for i, post in enumerate(previews):
            if args.get("content_type"):
                post["content_type_v2"] = ct
        order = assistant_store.create_order(
            tenant_id,
            app_id=app_id,
            action_type="create_posts",
            title=f"Crear {count} publicación(es) — {app_id}",
            channel=platform,
            count=count,
            preview=previews,
            payload={"posts": previews},
            prompt=prompt,
            user=user,
        )
        orders.append(order)
        ids = ", ".join(p.get("id", "?") for p in previews)
        return orders, f"OK: {count} borrador(es) creados ({ids}). Pendientes de aprobación en panel."
    return orders, f"Herramienta no implementada: {name}"


def _process_with_llm(
    tenant_id: str,
    prompt: str,
    ctx: dict[str, Any],
    *,
    user: str,
    chat_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    from Motor_Tecnico.accio_engine import assistant_llm

    aid = ctx["app_id"]
    ai_cfg = ctx.get("ai_config") or {}
    pending = assistant_store.list_pending_orders(tenant_id)
    system = assistant_llm.build_system_prompt(ctx, len(pending))
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    client_hist = assistant_llm.normalize_client_history(chat_history)
    if client_hist:
        messages.extend(client_hist)
    else:
        messages.extend(assistant_llm.audit_to_messages(tenant_id, limit=6))
    messages.append({"role": "user", "content": prompt})

    orders: list[dict[str, Any]] = []
    model = assistant_llm.resolve_model(tenant_id, ai_cfg)
    cost: float | None = None
    mode = "suggestion"

    msg, model, cost = assistant_llm.chat_completion(
        tenant_id, messages, ai_cfg=ai_cfg, tools=assistant_llm.ACTION_TOOLS
    )

    if msg.get("tool_calls"):
        messages.append(msg)
        for tc in msg["tool_calls"]:
            fn = tc.get("function") or {}
            fname = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            new_orders, tool_result = _execute_tool_call(fname, args, tenant_id, aid, user, prompt)
            orders.extend(new_orders)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.get("id"),
                    "content": tool_result,
                }
            )
        if orders:
            mode = "executable"
        final, model, cost2 = assistant_llm.chat_completion(tenant_id, messages, ai_cfg=ai_cfg, tools=None)
        cost = (cost or 0) + (cost2 or 0) if cost and cost2 else (cost2 or cost)
        response = (final.get("content") or "").strip()
    else:
        response = (msg.get("content") or "").strip()

    if not response:
        response = "Listo. Revisa el panel «Borradores pendientes» si pediste crear contenido."

    all_pending = list(pending)
    seen = {o["id"] for o in all_pending}
    for o in orders:
        if o["id"] not in seen:
            all_pending.insert(0, o)

    assistant_store.record_audit(
        tenant_id,
        user=user,
        app_id=aid,
        prompt=prompt,
        response=response,
        actions=[{"id": o["id"], "type": o["action_type"], "title": o["title"]} for o in orders],
        mode=mode,
        model=model,
        cost_estimate=cost,
        context_view=ctx.get("view", ""),
    )

    return {
        "ok": True,
        "mode": mode,
        "response": response,
        "orders": orders,
        "model": model,
        "llm": True,
        "pending_orders": all_pending,
    }


def _no_llm_message(tenant_id: str, ai_cfg: dict[str, Any] | None = None) -> str:
    from Motor_Tecnico.accio_engine import assistant_llm

    if not assistant_llm.assistant_enabled(ai_cfg):
        return (
            "El asistente IA está desactivado.\n"
            "Actívalo en Configuración → IA, o define AI_ASSISTANT_ENABLED=true en el servidor."
        )
    if not assistant_llm.resolve_openai_key(tenant_id):
        return (
            "Para chat conversacional necesitas la API Key de OpenAI (sk-…), distinta de ACCIO_API_KEY.\n\n"
            "Configuración → Variables → OpenAI API Key (IA)\n"
            "O en el servidor: OPENAI_API_KEY=sk-…\n\n"
            "Mientras tanto puedo ayudarte con órdenes: «Genera 1 publicación para LinkedIn», "
            "«Revisa la cola», «¿Dónde veo el borrador?»."
        )
    return "El asistente IA está deshabilitado en Configuración → IA. Actívalo para chat conversacional."


def process_message(
    tenant_id: str,
    prompt: str,
    *,
    app_id: str | None = None,
    user: str = "dashboard",
    view: str = "",
    selected_post_id: str | None = None,
    chat_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    from Motor_Tecnico.accio_engine import assistant_llm

    aid = marketing_app.normalize_app_id(app_id or marketing_app.default_app_id(tenant_id))
    ctx = build_context(tenant_id, aid, view=view, selected_post_id=selected_post_id)
    ctx["view"] = view
    ai_cfg = ctx["ai_config"]

    if assistant_llm.llm_available(tenant_id, ai_cfg):
        try:
            return _process_with_llm(tenant_id, prompt, ctx, user=user, chat_history=chat_history)
        except RuntimeError as exc:
            if "OPENAI_KEY_MISSING" in str(exc):
                pass
            else:
                err = str(exc)
                if "401" in err or "invalid_api_key" in err.lower():
                    return {
                        "ok": True,
                        "mode": "suggestion",
                        "response": "La API Key de OpenAI no es válida. Revísala en Configuración → Variables (debe empezar con sk-).",
                        "orders": [],
                        "model": "error",
                        "llm": False,
                        "error_code": "OPENAI_KEY_INVALID",
                        "pending_orders": assistant_store.list_pending_orders(tenant_id),
                    }
                # fallback rules on transient errors
                pass

    if not assistant_llm.resolve_openai_key(tenant_id):
        result = _process_rules(tenant_id, prompt, ctx, user=user, view=view)
        if result.get("response", "").startswith("No capté"):
            result["response"] = _no_llm_message(tenant_id, ai_cfg)
        result["llm"] = False
        result["error_code"] = "OPENAI_KEY_MISSING"
        return result

    if not assistant_llm.assistant_enabled(ai_cfg):
        return {
            "ok": True,
            "mode": "suggestion",
            "response": _no_llm_message(tenant_id, ai_cfg),
            "orders": [],
            "model": "disabled",
            "llm": False,
            "error_code": "ASSISTANT_DISABLED",
            "pending_orders": assistant_store.list_pending_orders(tenant_id),
        }

    result = _process_rules(tenant_id, prompt, ctx, user=user, view=view)
    result["llm"] = False
    return result


def _process_rules(
    tenant_id: str,
    prompt: str,
    ctx: dict[str, Any],
    *,
    user: str,
    view: str = "",
) -> dict[str, Any]:
    aid = ctx["app_id"]
    ai_cfg = ctx["ai_config"]
    lower = prompt.lower().strip()
    orders: list[dict[str, Any]] = []
    mode = "suggestion"
    response = ""
    model = "rules"
    cost: float | None = None

    target_app = _resolve_app_from_text(lower, aid)
    platform = _resolve_platform(lower)

    wants_advice = bool(re.search(r"\b(coment\w*|cuent\w*|explic\w*|qué opin|que opin)\b", lower))
    wants_create = bool(
        re.search(r"\b(crea|genera|prepara|encola|hazlo|haz la|hazme)\b", lower)
        and re.search(r"\b(publicacion|publicación|post|campaña|campana)\b", lower)
    )
    wants_where = bool(re.search(r"\b(donde|dónde|donde veo|dónde veo|ver la|ver el|vista previa|borrador)\b", lower))

    if wants_where:
        response = _where_to_see_posts(tenant_id, aid)

    elif "revisa la cola" in lower or "qué está débil" in lower or "que esta debil" in lower or "cola" in lower and "débil" in lower:
        response = _analyze_queue(ctx)

    elif wants_create and not wants_advice:
        count = _extract_count(lower, default=3 if "campaña" in lower or "campana" in lower else 1)
        topic_hint = "EM+Acción plataforma marketing" if re.search(r"emaccion|em\+accion|em accion", lower) else prompt[:80]
        previews = _generate_posts_preview(tenant_id, target_app, count, platform, topic_hint=topic_hint)
        order = assistant_store.create_order(
            tenant_id,
            app_id=target_app,
            action_type="create_posts",
            title=f"Crear {count} publicación(es) — {target_app}",
            channel=platform,
            count=count,
            preview=previews,
            payload={"posts": previews},
            prompt=prompt,
            user=user,
        )
        orders.append(order)
        mode = "executable"
        prev_id = previews[0]["id"] if previews else "—"
        response = (
            f"Listo: {count} borrador(es) para {target_app} ({platform}).\n\n"
            f"↓ Míralo abajo en «Borradores pendientes» (entre el chat y el cuadro de texto).\n"
            f"ID: {prev_id}\n\n"
            "1. Revisa el texto en la tarjeta\n"
            "2. Pulsa Aprobar → entra a la cola\n"
            "3. Ve a Publicaciones o Campañas para programar/publicar"
        )

    elif wants_advice or (
        re.search(r"quiero crear", lower) and re.search(r"emaccion|em\+accion|em accion|em\+acción", lower)
    ):
        if re.search(r"emaccion|em\+accion|em accion|em\+acción", lower):
            response = _emaccion_marketing_advice()
        else:
            response = (
                f"Para {target_app}: combina 3 posts de valor (problema + tip) por cada 1 de venta (demo/CTA). "
                f"Canal sugerido: {platform}. "
                "Cuando quieras el borrador concreto, di «Genera 1 publicación»."
            )

    elif "reescribe" in lower or "reescrib" in lower:
        post = ctx.get("selected_post")
        if not post:
            response = "Selecciona una publicación en el panel izquierdo y vuelve a pedir la reescritura."
        else:
            tone = "ejecutivo" if "ejecutiv" in lower else "cercano"
            new_text = (post.get("text") or "")[:400]
            if ai_cfg.get("topic_model") == "llm" and ai_cfg.get("enabled", True):
                llm_text, model, cost = _call_openai(
                    f"Reescribe este post con tono {tone}:\n\n{post.get('text')}",
                    "Eres copywriter B2B para Panamá. Mantén CTA y hashtags.",
                    tenant_id,
                    ai_cfg,
                )
                if llm_text:
                    new_text = llm_text
            else:
                new_text = f"[Tono {tone}]\n\n" + (post.get("text") or "")
            preview_post = {**post, "id": f"{post['id']}_variant_{uuid.uuid4().hex[:6]}", "text": new_text, "status": "draft"}
            order = assistant_store.create_order(
                tenant_id,
                app_id=post.get("app_id", aid),
                action_type="rewrite_post",
                title=f"Reescribir — {post.get('id')}",
                channel=post.get("platform", platform),
                count=1,
                preview=[preview_post],
                payload={"source_id": post.get("id"), "post": preview_post},
                prompt=prompt,
                user=user,
            )
            orders.append(order)
            mode = "executable"
            response = "Generé una variante reescrita. Aprueba para encolarla como borrador."

    elif "duplica" in lower and re.search(r"facebook|instagram|linkedin", lower):
        post = ctx.get("selected_post")
        if not post:
            response = "Selecciona la publicación a duplicar."
        else:
            order = assistant_store.create_order(
                tenant_id,
                app_id=post.get("app_id", aid),
                action_type="duplicate_platform",
                title=f"Duplicar a {platform}",
                channel=platform,
                count=1,
                preview=[{**post, "platform": platform, "status": "draft"}],
                payload={"source_id": post.get("id"), "platform": platform},
                prompt=prompt,
                user=user,
            )
            orders.append(order)
            mode = "executable"
            response = f"Orden lista: duplicar «{post.get('id')}» para {platform}."

    elif "resume" in lower and ("mes" in lower or "publicado" in lower):
        response = _summarize_month(ctx)

    elif re.search(r"\b(hola|activo|activa|cargad|estas ahí|estas ahi|funcionas|lista)\b", lower):
        response = (
            f"Sí, estoy activa para la app «{aid}» (tenant {tenant_id}). "
            "Puedo crear borradores, reescribir posts, analizar la cola o resumir publicaciones. "
            "Los borradores aparecen abajo en «Borradores pendientes». Nada se publica sin tu aprobación."
        )

    elif "analiza" in lower and ("métrica" in lower or "metrica" in lower or "resultado" in lower):
        counts = ctx.get("status_counts") or {}
        response = f"Estado de publicaciones: {counts}. " + _summarize_month(ctx)

    elif "ideas" in lower or "genera ideas" in lower:
        slug = _product_slug(target_app)
        response = f"Ideas para {target_app}: checklist operativo, error común del sector, caso breve, demo CTA, tendencia Panamá 2026. ¿Genero borradores? Di «Crea 5 publicaciones sobre {target_app}»."

    else:
        pending_n = len(assistant_store.list_pending_orders(tenant_id))
        hint = f"\n\nTienes {pending_n} borrador(es) pendientes abajo." if pending_n else ""
        response = (
            "No capté una orden concreta. Prueba:\n"
            "• «Genera 1 publicación de EM+Acción para LinkedIn»\n"
            "• «¿Dónde veo el borrador?»\n"
            "• «Coméntame cómo promocionar EM+Acción»\n"
            "• «Revisa la cola»"
            + hint
        )

    all_pending = assistant_store.list_pending_orders(tenant_id)
    # Incluir órdenes recién creadas aunque el filtro por app no las devuelva
    seen = {o["id"] for o in all_pending}
    for o in orders:
        if o["id"] not in seen:
            all_pending.insert(0, o)

    assistant_store.record_audit(
        tenant_id,
        user=user,
        app_id=aid,
        prompt=prompt,
        response=response,
        actions=[{"id": o["id"], "type": o["action_type"], "title": o["title"]} for o in orders],
        mode=mode,
        model=model,
        cost_estimate=cost,
        context_view=view,
    )

    return {
        "ok": True,
        "mode": mode,
        "response": response,
        "orders": orders,
        "model": model,
        "llm": False,
        "pending_orders": all_pending,
    }


def approve_order(tenant_id: str, order_id: str, *, user: str = "dashboard") -> dict[str, Any]:
    order = assistant_store.get_order(tenant_id, order_id)
    if not order:
        raise ValueError(f"Orden no encontrada: {order_id}")
    if order.get("status") != "pending_approval":
        raise ValueError("La orden ya fue resuelta")

    pub_settings = settings_center.load_publication(tenant_id)
    auto = bool(pub_settings.get("auto_publish"))
    action = order.get("action_type")
    result: dict[str, Any] = {"created": [], "auto_publish": auto}

    if action == "create_posts":
        posts = order.get("payload", {}).get("posts") or order.get("preview") or []
        for post in posts:
            post = dict(post)
            post["app_id"] = order.get("app_id")
            post["status"] = "scheduled" if auto else "pending_approval"
            post["created_at"] = datetime.now(PANAMA).isoformat()
            post["author"] = user
            created = executor.enqueue_post(post, tenant_id, app_id=order.get("app_id"))
            result["created"].append(created)

    elif action == "rewrite_post":
        post = order.get("payload", {}).get("post") or (order.get("preview") or [{}])[0]
        post = dict(post)
        post["status"] = "draft"
        post["author"] = user
        result["created"] = [executor.enqueue_post(post, tenant_id, app_id=order.get("app_id"))]

    elif action == "duplicate_platform":
        source_id = order.get("payload", {}).get("source_id")
        platform = order.get("payload", {}).get("platform") or order.get("channel")
        dup = publications_api.duplicate_publication(
            tenant_id, source_id, app_id=order.get("app_id"), platform=platform, author=user
        )
        result["created"] = [dup]

    else:
        raise ValueError(f"Tipo de orden no soportado: {action}")

    assistant_store.update_order_status(tenant_id, order_id, "approved", result=result)
    return {"ok": True, "order_id": order_id, "result": result}


def reject_order(tenant_id: str, order_id: str) -> dict[str, Any]:
    assistant_store.update_order_status(tenant_id, order_id, "rejected")
    return {"ok": True, "order_id": order_id, "status": "rejected"}
