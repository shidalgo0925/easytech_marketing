#!/usr/bin/env python3
"""Apps de marketing dentro de un tenant (Fase App — EMAcción SaaS)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from Motor_Tecnico.accio_engine.tenant import DEFAULT_TENANT, effective_paths, resolve_tenant

_APP_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{1,48}$")
DEFAULT_APP_ID = "default"

# Mapeo products.json (easytech) → app_id canónico
_PRODUCT_SLUG_TO_APP: dict[str, str] = {
    "easynodeone_en1_plataforma_todo_en_uno": "en1",
    "epayroll_planilla_panam": "epayroll",
    "eposone_punto_de_venta_e_inventario": "eposone",
    "eclassone_gesti_n_acad_mica": "eclassone",
    "ethesisone_tesis_universitarias": "ethesisone",
    "odoo_erp_facturaci_n_electr_nica_dgi": "odoo-fe",
    "consultor_a_ti_estrat_gica": "consultoria",
    "desarrollo_de_software_a_medida": "desarrollo",
}


class AppNotFoundError(KeyError):
    pass


@dataclass(frozen=True)
class MarketingApp:
    app_id: str
    tenant_id: str
    name: str
    slug: str
    status: str
    is_default: bool
    description: str = ""
    tone: str = ""
    target_audience: str = ""
    logo_url: str = ""
    brand_colors: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "app_id": self.app_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "slug": self.slug,
            "status": self.status,
            "is_default": self.is_default,
            "description": self.description,
            "tone": self.tone,
            "target_audience": self.target_audience,
            "logo_url": self.logo_url,
            "brand_colors": self.brand_colors or {},
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def apps_root(tenant_id: str) -> Path:
    return resolve_tenant(tenant_id).root / "apps"


def registry_path(tenant_id: str) -> Path:
    return apps_root(tenant_id) / "registry.json"


def normalize_app_id(app_id: str | None) -> str:
    aid = (app_id or DEFAULT_APP_ID).strip().lower()
    if not _APP_ID_RE.match(aid):
        raise AppNotFoundError(f"app_id inválido: {app_id}")
    return aid


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _app_from_record(tenant_id: str, raw: dict[str, Any]) -> MarketingApp:
    return MarketingApp(
        app_id=raw["app_id"],
        tenant_id=tenant_id,
        name=raw.get("name", raw["app_id"]),
        slug=raw.get("slug", raw["app_id"]),
        status=raw.get("status", "active"),
        is_default=bool(raw.get("is_default")),
        description=raw.get("description", ""),
        tone=raw.get("tone", ""),
        target_audience=raw.get("target_audience", ""),
        logo_url=raw.get("logo_url", ""),
        brand_colors=dict(raw.get("brand_colors") or {}),
    )


def _default_app_record(tenant_id: str) -> dict[str, Any]:
    tenant = resolve_tenant(tenant_id)
    return {
        "app_id": DEFAULT_APP_ID,
        "name": tenant.display_name,
        "slug": DEFAULT_APP_ID,
        "status": "active",
        "is_default": True,
        "description": "Marca principal y contenido general del tenant",
    }


def _apps_from_products(tenant_id: str) -> list[dict[str, Any]]:
    products_path = resolve_tenant(tenant_id).root / "products.json"
    if not products_path.is_file():
        return []
    try:
        data = json.loads(products_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    apps: list[dict[str, Any]] = []
    for row in data.get("products", []):
        if not row.get("enabled", True):
            continue
        slug = row.get("slug") or ""
        app_id = _PRODUCT_SLUG_TO_APP.get(slug) or re.sub(r"[^a-z0-9_-]+", "-", slug.lower())[:48].strip("-")
        if not app_id or app_id == DEFAULT_APP_ID:
            continue
        apps.append(
            {
                "app_id": app_id,
                "name": row.get("name", app_id),
                "slug": app_id,
                "status": "active",
                "is_default": False,
                "description": "",
                "product_slug": slug,
            }
        )
    return apps


def bootstrap_registry(tenant_id: str, *, force: bool = False) -> dict[str, Any]:
    """Crea apps/registry.json si no existe (idempotente)."""
    path = registry_path(tenant_id)
    if path.is_file() and not force:
        return json.loads(path.read_text(encoding="utf-8"))

    default = _default_app_record(tenant_id)
    product_apps = _apps_from_products(tenant_id) if tenant_id == DEFAULT_TENANT else []
    seen = {DEFAULT_APP_ID}
    apps = [default]
    for row in product_apps:
        if row["app_id"] in seen:
            continue
        seen.add(row["app_id"])
        apps.append(row)

    payload = {
        "version": 1,
        "updated_at": _utc_now(),
        "default_app_id": DEFAULT_APP_ID,
        "apps": apps,
    }
    _write_json(path, payload)
    return payload


def load_registry(tenant_id: str) -> dict[str, Any]:
    path = registry_path(tenant_id)
    if not path.is_file():
        return bootstrap_registry(tenant_id)
    return json.loads(path.read_text(encoding="utf-8"))


def default_app_id(tenant_id: str) -> str:
    reg = load_registry(tenant_id)
    return reg.get("default_app_id") or DEFAULT_APP_ID


def list_apps(tenant_id: str, *, active_only: bool = True) -> list[MarketingApp]:
    reg = load_registry(tenant_id)
    items: list[MarketingApp] = []
    for raw in reg.get("apps", []):
        if active_only and raw.get("status") != "active":
            continue
        items.append(_app_from_record(tenant_id, raw))
    return sorted(items, key=lambda a: (not a.is_default, a.name.lower()))


def get_app(tenant_id: str, app_id: str) -> MarketingApp:
    aid = normalize_app_id(app_id)
    for app in list_apps(tenant_id, active_only=False):
        if app.app_id == aid:
            if app.status != "active":
                raise AppNotFoundError(f"App deshabilitada: {aid}")
            return app
    raise AppNotFoundError(f"App no encontrada: {aid} en tenant {tenant_id}")


def resolve_app(tenant_id: str, app_id: str | None = None) -> MarketingApp:
    aid = normalize_app_id(app_id or default_app_id(tenant_id))
    return get_app(tenant_id, aid)


def create_app(tenant_id: str, payload: dict[str, Any]) -> MarketingApp:
    aid = normalize_app_id(payload.get("app_id") or payload.get("slug") or "")
    reg = load_registry(tenant_id)
    if any(a.get("app_id") == aid for a in reg.get("apps", [])):
        raise ValueError(f"Ya existe una app con ID «{aid}»")
    name = (payload.get("name") or aid).strip()
    if not name:
        raise ValueError("Nombre de app obligatorio")
    record = {
        "app_id": aid,
        "name": name,
        "slug": payload.get("slug") or aid,
        "status": "active",
        "is_default": False,
        "description": payload.get("description", ""),
        "tone": payload.get("tone", ""),
        "target_audience": payload.get("target_audience", ""),
        "logo_url": payload.get("logo_url", ""),
        "brand_colors": payload.get("brand_colors") or {},
    }
    reg.setdefault("apps", []).append(record)
    reg["updated_at"] = _utc_now()
    _write_json(registry_path(tenant_id), reg)
    app_dir = apps_root(tenant_id) / aid
    app_dir.mkdir(parents=True, exist_ok=True)
    for fname, empty in (
        ("content_queue.json", {"posts": []}),
        ("campaigns.json", {"campaigns": []}),
        ("calendar.json", {"weeks": []}),
    ):
        p = app_dir / fname
        if not p.is_file():
            _write_json(p, empty)
    return get_app(tenant_id, aid)


def effective_app_paths(tenant_id: str, app_id: str | None = None) -> dict[str, Path]:
    """Paths de datos; app default usa raíz del tenant (compatibilidad)."""
    aid = normalize_app_id(app_id or default_app_id(tenant_id))
    base = effective_paths(resolve_tenant(tenant_id))
    if aid == DEFAULT_APP_ID or aid == default_app_id(tenant_id):
        return {**base, "app_id": aid, "app_root": resolve_tenant(tenant_id).root}
    root = apps_root(tenant_id) / aid
    root.mkdir(parents=True, exist_ok=True)
    return {
        "app_id": aid,
        "app_root": root,
        "content_queue": root / "content_queue.json",
        "calendar": root / "calendar.json",
        "campaigns": root / "campaigns.json",
        "knowledge_dir": root / "knowledge",
        "flyers_dir": root / "flyers",
    }


def ensure_post_app_ids(tenant_id: str = DEFAULT_TENANT, app_id: str | None = None) -> int:
    """Añade app_id a posts sin campo (migración suave)."""
    paths = effective_app_paths(tenant_id, app_id)
    qpath = paths.get("content_queue")
    if not qpath or not qpath.is_file():
        return 0
    data = json.loads(qpath.read_text(encoding="utf-8"))
    default = default_app_id(tenant_id)
    changed = 0
    for post in data.get("posts", []):
        if not post.get("app_id"):
            post["app_id"] = default
            changed += 1
    if changed:
        _write_json(qpath, data)
    return changed
