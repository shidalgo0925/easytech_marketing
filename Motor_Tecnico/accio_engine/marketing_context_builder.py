"""Marketing Context Builder V1 — Vertical Slice 1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from Motor_Tecnico.accio_engine import knowledge_api, marketing_app
from Motor_Tecnico.accio_engine.marketing_plan_application.context import ApplicationContext
from Motor_Tecnico.accio_engine.marketing_plan_application.query_inputs import GetActiveMarketingPlanQuery
from Motor_Tecnico.accio_engine.marketing_plan_api.composition import marketing_plan_use_cases
from Motor_Tecnico.accio_engine.marketing_plan_api.dto import plan_to_response


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_app_profile(tenant_id: str, app_id: str) -> dict[str, Any]:
    paths = marketing_app.effective_app_paths(tenant_id, app_id)
    profile = _read_json(paths["profile"])
    app = marketing_app.get_app(tenant_id, app_id)
    return {
        "app_id": app.app_id,
        "name": app.name,
        "description": app.description,
        "tone": app.tone or profile.get("tone"),
        "target_audience": app.target_audience or profile.get("target_audience"),
        "brand_colors": app.brand_colors or profile.get("brand_colors") or {},
        "profile": profile,
    }


def _load_knowledge_excerpt(tenant_id: str, app_id: str, *, max_chars: int = 12000) -> list[dict[str, Any]]:
    paths = marketing_app.effective_app_paths(tenant_id, app_id)
    kdir = paths["knowledge_dir"]
    items: list[dict[str, Any]] = []
    total = 0
    if not kdir.is_dir():
        return items
    for path in sorted(kdir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        chunk = text[: max_chars - total]
        items.append({"id": path.stem, "title": path.stem, "excerpt": chunk})
        total += len(chunk)
        if total >= max_chars:
            break
    return items


def build_marketing_context(
    tenant_id: str,
    app_id: str,
    *,
    actor_id: str = "system",
    actor_role: str = "admin",
) -> dict[str, Any]:
    """Business Context + App Profile + KB + Plan activo → contexto final (VS1 compat)."""
    from Motor_Tecnico.accio_engine.marketing_context_engine import get_marketing_context_builder
    from Motor_Tecnico.accio_engine.marketing_plan_application.context import ApplicationContext
    from Motor_Tecnico.accio_engine.marketing_plan_application.query_inputs import GetActiveMarketingPlanQuery
    from Motor_Tecnico.accio_engine.marketing_plan_api.composition import marketing_plan_use_cases
    from Motor_Tecnico.accio_engine.marketing_plan_api.dto import plan_to_response

    base = get_marketing_context_builder().build(tenant_id, app_id=app_id)
    app_profile = _load_app_profile(tenant_id, app_id)
    knowledge = _load_knowledge_excerpt(tenant_id, app_id)

    active_plan = None
    ctx = ApplicationContext(
        tenant_id=tenant_id,
        app_id=app_id,
        actor_id=actor_id,
        actor_role=actor_role,
    )
    use_cases = marketing_plan_use_cases()
    try:
        plan = use_cases.get_active(ctx, GetActiveMarketingPlanQuery())
        if plan:
            active_plan = plan_to_response(plan)
    except Exception:
        active_plan = None

    return {
        **base,
        "business_context": base.get("company_brain") or knowledge_api.load_business_context(tenant_id),
        "app_profile": app_profile,
        "knowledge_base": knowledge,
        "marketing_plan_active": active_plan,
        "builder_version": "v1-slice+mce",
    }
