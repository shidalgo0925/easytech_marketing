"""Marketing Planner V1 — 3 propuestas desde contexto (Vertical Slice 1)."""

from __future__ import annotations

import json
import re
from typing import Any

from Motor_Tecnico.accio_engine import assistant_llm, knowledge_api
from Motor_Tecnico.accio_engine.marketing_context_builder import build_marketing_context


def _fallback_proposals(context: dict[str, Any]) -> list[dict[str, Any]]:
    plan = context.get("marketing_plan_active") or {}
    nombre = plan.get("nombre") or "Plan de marketing"
    objetivo = plan.get("objetivo_general") or "Fortalecer presencia en el mercado"
    north = plan.get("north_star_metric") or "Indicador principal"
    return [
        {
            "title": f"Contenido educativo alineado a {nombre}",
            "summary": f"Serie de piezas de valor que refuercen: {objetivo[:120]}",
            "channel_hint": "LinkedIn",
            "priority": "alta",
            "actions": [
                "Definir 3 pilares de contenido alineados al objetivo",
                "Programar calendario editorial de 4 semanas",
                "Medir engagement vs. north star: " + str(north)[:60],
            ],
            "rationale": "Prioriza awareness consultivo antes de CTA comercial directo.",
        },
        {
            "title": "Caso de uso / prueba social",
            "summary": "Destacar un resultado medible relacionado con la north star del plan.",
            "channel_hint": "LinkedIn",
            "priority": "media",
            "actions": [
                "Seleccionar 1 caso cliente verificable",
                "Estructurar narrativa problema → solución → resultado",
                "Publicar con CTA suave a diagnóstico",
            ],
            "rationale": "Reduce fricción de confianza en segmento PYME.",
        },
        {
            "title": "CTA diagnóstico consultivo",
            "summary": "Invitar a conversación alineada al CTA institucional DIAGNÓSTICO.",
            "channel_hint": "Email / LinkedIn",
            "priority": "media",
            "actions": [
                "Redactar invitación con beneficio concreto",
                "Enlazar guía institucional y WhatsApp",
                "Segmentar lista cálida vs. fría",
            ],
            "rationale": "Cierra el ciclo valor → conversación sin hard sell.",
        },
    ]


def _executive_summary(context: dict[str, Any], proposals: list[dict[str, Any]]) -> str:
    plan = context.get("marketing_plan_active") or {}
    app = (context.get("app_profile") or {}).get("name") or context.get("app_id") or "App"
    nombre = plan.get("nombre") or "sin plan activo"
    objetivo = plan.get("objetivo_general") or "Consolidar posicionamiento"
    kb = len(context.get("knowledge_base") or [])
    top = proposals[0]["title"] if proposals else "contenido educativo"
    return (
        f"Para {app}, el plan «{nombre}» apunta a {objetivo[:140]}. "
        f"Con {kb} fuentes de conocimiento disponibles, la recomendación prioritaria es "
        f"«{top}», equilibrando valor editorial y conversión consultiva."
    )


def _normalize_proposal(row: dict[str, Any]) -> dict[str, Any]:
    actions = row.get("actions") or []
    if isinstance(actions, str):
        actions = [actions]
    return {
        "title": str(row.get("title") or ""),
        "summary": str(row.get("summary") or ""),
        "channel_hint": str(row.get("channel_hint") or ""),
        "priority": str(row.get("priority") or "media"),
        "actions": [str(a) for a in actions if a][:5],
        "rationale": str(row.get("rationale") or ""),
    }


def _parse_proposals(text: str) -> list[dict[str, Any]] | None:
    text = text.strip()
    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list):
        return None
    out: list[dict[str, Any]] = []
    for row in data[:3]:
        if isinstance(row, dict) and row.get("title"):
            out.append(_normalize_proposal(row))
    return out if len(out) >= 1 else None


def generate_proposals(
    tenant_id: str,
    app_id: str,
    *,
    actor_id: str = "system",
    actor_role: str = "admin",
) -> dict[str, Any]:
    ai_cfg = knowledge_api.load_business_context(tenant_id).get("ai") or {}
    context = build_marketing_context(tenant_id, app_id, actor_id=actor_id, actor_role=actor_role)

    if not assistant_llm.llm_available(tenant_id, ai_cfg if isinstance(ai_cfg, dict) else None):
        proposals = _fallback_proposals(context)
        return {
            "mode": "fallback",
            "executive_summary": _executive_summary(context, proposals),
            "proposals": proposals,
            "context_snapshot": {
                "has_active_plan": bool(context.get("marketing_plan_active")),
                "knowledge_articles": len(context.get("knowledge_base") or []),
            },
        }

    prompt_context = {
        "business_context": context.get("business_context"),
        "app_profile": context.get("app_profile"),
        "knowledge_topics": [k.get("id") for k in (context.get("knowledge_base") or [])],
        "marketing_plan_active": context.get("marketing_plan_active"),
    }
    system = (
        "Eres el Planner de marketing EM+Acción. Genera propuestas estratégicas declarativas. "
        "Responde SOLO con JSON: objeto con executive_summary (string) y proposals (lista de 3 objetos). "
        "Cada propuesta: title, summary, channel_hint, priority (alta|media|baja), "
        "actions (lista de 3 strings), rationale."
    )
    user = f"Contexto:\n{json.dumps(prompt_context, ensure_ascii=False, indent=2)}"
    try:
        msg, model_name, _cost = assistant_llm.chat_completion(
            tenant_id,
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            model=assistant_llm.resolve_model(tenant_id, ai_cfg if isinstance(ai_cfg, dict) else None),
            ai_cfg=ai_cfg if isinstance(ai_cfg, dict) else None,
        )
        text = (msg.get("content") or "").strip()
    except RuntimeError:
        proposals = _fallback_proposals(context)
        return {
            "mode": "fallback",
            "executive_summary": _executive_summary(context, proposals),
            "proposals": proposals,
            "context_snapshot": {
                "has_active_plan": bool(context.get("marketing_plan_active")),
                "knowledge_articles": len(context.get("knowledge_base") or []),
            },
        }
    exec_summary = None
    proposals: list[dict[str, Any]] | None = None
    obj_match = re.search(r"\{[\s\S]*\}", text)
    if obj_match:
        try:
            parsed = json.loads(obj_match.group(0))
            if isinstance(parsed, dict):
                exec_summary = parsed.get("executive_summary")
                raw = parsed.get("proposals")
                if isinstance(raw, list):
                    proposals = [_normalize_proposal(r) for r in raw if isinstance(r, dict) and r.get("title")]
        except json.JSONDecodeError:
            pass
    if not proposals:
        proposals = _parse_proposals(text)
    if not proposals:
        proposals = _fallback_proposals(context)
    while len(proposals) < 3:
        proposals.extend(_fallback_proposals(context))
    return {
        "mode": "llm",
        "executive_summary": exec_summary or _executive_summary(context, proposals[:3]),
        "proposals": proposals[:3],
        "context_snapshot": {
            "has_active_plan": bool(context.get("marketing_plan_active")),
            "knowledge_articles": len(context.get("knowledge_base") or []),
        },
    }
