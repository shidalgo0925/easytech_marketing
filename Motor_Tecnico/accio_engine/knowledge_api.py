#!/usr/bin/env python3
"""Fase E — contexto de negocio, knowledge base y generador de temas."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PANAMA = ZoneInfo("America/Panama")

BUSINESS_CONTEXT_PATH = BASE_DIR / "Marketing" / "accio" / "business_context.json"
EDITORIAL_RULES_PATH = BASE_DIR / "Marketing" / "accio" / "editorial_rules.json"
KNOWLEDGE_DIR = BASE_DIR / "Marketing" / "knowledge"
KNOWLEDGE_MANIFEST_PATH = KNOWLEDGE_DIR / "manifest.json"

PRODUCT_FLYER = {
    "easytech": 11,
    "odoo_fe": 3,
    "en1": 5,
    "eposone": 8,
    "eclassone": 6,
    "epayroll": 9,
    "casos_exito": 12,
    "faqs": 11,
    "general": 11,
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_business_context() -> dict[str, Any]:
    if not BUSINESS_CONTEXT_PATH.is_file():
        return {}
    return _read_json(BUSINESS_CONTEXT_PATH)


def save_business_context(payload: dict[str, Any]) -> dict[str, Any]:
    current = load_business_context()
    allowed = {
        "empresa",
        "industria",
        "pais",
        "publico_objetivo",
        "productos_servicios",
        "diferenciadores",
        "problemas_que_resuelve",
        "tono_comunicacion",
        "objetivos_comerciales",
        "cta_principal",
        "contacto",
    }
    for key in allowed:
        if key in payload:
            current[key] = payload[key]
    current["version"] = current.get("version", 1)
    current["updated_at"] = datetime.now(PANAMA).strftime("%Y-%m-%d")
    _write_json(BUSINESS_CONTEXT_PATH, current)
    return current


def load_editorial_rules() -> dict[str, Any]:
    if not EDITORIAL_RULES_PATH.is_file():
        return {}
    return _read_json(EDITORIAL_RULES_PATH)


def load_knowledge_manifest() -> dict[str, Any]:
    if not KNOWLEDGE_MANIFEST_PATH.is_file():
        return {"articles": []}
    return _read_json(KNOWLEDGE_MANIFEST_PATH)


def _parse_md_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = "_intro"
    buf: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if buf:
                sections[current] = "\n".join(buf).strip()
            current = line[3:].strip().lower()
            buf = []
        else:
            buf.append(line)
    if buf:
        sections[current] = "\n".join(buf).strip()
    return sections


def load_article(slug: str) -> dict[str, Any]:
    manifest = load_knowledge_manifest()
    entry = next((a for a in manifest.get("articles", []) if a.get("slug") == slug), None)
    if not entry:
        raise FileNotFoundError(f"Artículo no encontrado: {slug}")
    path = KNOWLEDGE_DIR / entry["file"]
    if not path.is_file():
        raise FileNotFoundError(f"Archivo KB faltante: {entry['file']}")
    body = path.read_text(encoding="utf-8")
    return {
        **entry,
        "body": body,
        "sections": _parse_md_sections(body),
    }


def list_knowledge() -> list[dict[str, Any]]:
    manifest = load_knowledge_manifest()
    items = []
    for entry in manifest.get("articles", []):
        path = KNOWLEDGE_DIR / entry["file"]
        items.append(
            {
                "slug": entry.get("slug"),
                "title": entry.get("title"),
                "product": entry.get("product"),
                "tags": entry.get("tags", []),
                "file": entry.get("file"),
                "available": path.is_file(),
                "chars": len(path.read_text(encoding="utf-8")) if path.is_file() else 0,
            }
        )
    return items


def _contact_block(ctx: dict[str, Any]) -> str:
    contact = ctx.get("contacto") or {}
    email = contact.get("email", "easytechservices25@gmail.com")
    wa = contact.get("whatsapp", "+507 6688-4938")
    guia = contact.get("guia", "https://n8n.etsrv.site/guia/")
    return f"📩 {email}\n📱 WhatsApp: {wa}\n📄 Guía: {guia}"


def _hashtags_for(product: str, content_type: str) -> str:
    base = ["#Panama", "#PYME", "#EasyTech", "#TransformacionDigital"]
    extra = {
        "odoo_fe": ["#Odoo", "#FacturacionElectronica", "#DGI", "#ERP"],
        "en1": ["#EN1", "#EasyNodeOne", "#ERP"],
        "eposone": ["#Retail", "#Inventario", "#EPOSOne"],
        "eclassone": ["#EdTech", "#Educacion", "#EClassOne"],
        "epayroll": ["#Planilla", "#RRHH", "#EPayRoll"],
        "casos_exito": ["#CasosDeExito", "#ConsultoriaTI"],
        "faqs": ["#DiagnosticoTecnologico"],
        "easytech": ["#ConsultoriaTI"],
    }
    tags = base + extra.get(product, [])
    if content_type in ("consejo", "educacion", "valor"):
        tags.append("#ContenidoDeValor")
    return " ".join(dict.fromkeys(tags))


def _normalize_content_type(content_type: str) -> str:
    ct = (content_type or "educacion").strip().lower()
    legacy = {"valor": "educacion", "venta": "venta"}
    return legacy.get(ct, ct)


def _section_lines(sections: dict[str, str], *keys: str) -> list[str]:
    for key in keys:
        val = sections.get(key.lower(), "").strip()
        if val:
            return [ln.strip("- ").strip() for ln in val.splitlines() if ln.strip()]
    return []


def generate_topic(
    *,
    topic: str | None = None,
    product_slug: str = "easytech",
    content_type: str = "educacion",
    platform: str = "linkedin",
) -> dict[str, Any]:
    ctx = load_business_context()
    article = load_article(product_slug)
    sections = article["sections"]
    ct = _normalize_content_type(content_type)
    title = (topic or "").strip() or article.get("title") or "Tema sin título"

    problem = _section_lines(sections, "problema")[0] if _section_lines(sections, "problema") else ""
    explanation = _section_lines(sections, "explicación", "explicacion")
    solution = _section_lines(sections, "solución", "solucion")
    recommendation = _section_lines(sections, "recomendación", "recomendacion")
    errors = _section_lines(sections, "errores comunes", "señales de alerta")
    checklist = _section_lines(sections, "checklist quincena", "checklist pre-implementación")

    cta = ctx.get("cta_principal", "DIAGNÓSTICO")
    if ct == "venta":
        cta_line = f"🚀 Comenta {cta} o DEMO por DM."
    elif ct == "consejo":
        cta_line = f"💡 Guarda este post. ¿Te aplica? Comenta abajo."
    else:
        cta_line = f"¿Te resuena? Comenta o escríbeme {cta}."

    lines: list[str] = [f"{title} 🇵🇦", ""]
    if problem:
        lines += [problem, ""]
    if explanation:
        lines.append(explanation[0])
        lines.append("")
    if errors and ct in ("educacion", "valor", "tendencia"):
        lines.append("Errores que vemos seguido:")
        for i, err in enumerate(errors[:3], 1):
            lines.append(f"{i}️⃣ {err}")
        lines.append("")
    if checklist and ct == "consejo":
        lines.append("Checklist rápido:")
        for i, item in enumerate(checklist[:5], 1):
            lines.append(f"{i}. {item}")
        lines.append("")
    elif solution:
        lines.append("Qué funciona en la práctica:")
        for item in solution[:4]:
            lines.append(f"✅ {item}")
        lines.append("")
    if recommendation:
        lines.append(f"💡 {recommendation[0]}")
        lines.append("")
    lines.append(cta_line)
    lines.append("")
    lines.append(_contact_block(ctx))
    lines.append("")
    lines.append(_hashtags_for(article.get("product", product_slug), ct))

    text = "\n".join(lines)
    product = article.get("product", product_slug)
    flyer_num = PRODUCT_FLYER.get(product_slug) or PRODUCT_FLYER.get(product) or 11
    manifest_path = BASE_DIR / "Marketing" / "flyers" / "manifest.json"
    manifest = _read_json(manifest_path) if manifest_path.is_file() else {"flyers": []}
    flyer_entry = next((f for f in manifest.get("flyers", []) if f.get("num") == flyer_num), None)
    flyer_name = flyer_entry.get("file") if flyer_entry else "11_diagnostico_gratuito.png"

    legacy_type = "venta" if ct == "venta" else "valor"
    first_comment = None
    if ct != "venta":
        first_comment = "Guía técnica y diagnóstico sin costo 👇\nhttps://n8n.etsrv.site/guia/"

    slug_safe = re.sub(r"[^a-z0-9]+", "_", title.lower())[:40].strip("_")
    post_id = f"{platform}_{datetime.now(PANAMA).strftime('%Y%m%d')}_{slug_safe}"

    return {
        "topic": title,
        "product_slug": product_slug,
        "content_type": ct,
        "legacy_content_type": legacy_type,
        "platform": platform,
        "topic_framework": {
            "problem": problem or (_section_lines(sections, "problema")[0] if _section_lines(sections, "problema") else ""),
            "explanation": explanation[0] if explanation else "",
            "solution": solution[:4],
            "recommendation": recommendation[0] if recommendation else "",
        },
        "post": {
            "id": post_id,
            "platform": platform,
            "status": "pending",
            "content_type": legacy_type,
            "content_type_v2": ct,
            "topic_framework": {
                "problem": problem,
                "explanation": explanation[0] if explanation else "",
                "solution": solution[:4],
                "recommendation": recommendation[0] if recommendation else "",
            },
            "scheduled_at": datetime.now(PANAMA).replace(hour=13, minute=0, second=0, microsecond=0).isoformat(),
            "flyer": f"flyers/{flyer_name}",
            "flyer_num": flyer_num,
            "utm": f"{platform}_generated",
            "text": text,
            "first_comment": first_comment,
        },
        "sources": [product_slug],
    }


def editorial_balance(queue_posts: list[dict[str, Any]]) -> dict[str, Any]:
    rules = load_editorial_rules()
    pending = [p for p in queue_posts if p.get("status") == "pending"]
    counts: dict[str, int] = {"valor": 0, "venta": 0}
    for p in pending:
        ct = p.get("content_type_v2") or p.get("content_type") or "valor"
        if ct == "venta":
            counts["venta"] += 1
        else:
            counts["valor"] += 1
    total = max(len(pending), 1)
    return {
        "rules": rules,
        "pending_total": len(pending),
        "current": {
            "valor": counts["valor"],
            "venta": counts["venta"],
            "valor_pct": round(counts["valor"] / total * 100),
            "venta_pct": round(counts["venta"] / total * 100),
        },
        "next_suggested": "valor" if counts["venta"] >= counts["valor"] // 3 else "valor",
        "target": rules.get("target_matrix", {}),
    }


def knowledge_summary() -> dict[str, Any]:
    articles = list_knowledge()
    return {
        "business_context": load_business_context(),
        "editorial_rules": load_editorial_rules(),
        "articles": articles,
        "articles_count": len(articles),
        "articles_available": sum(1 for a in articles if a.get("available")),
    }
