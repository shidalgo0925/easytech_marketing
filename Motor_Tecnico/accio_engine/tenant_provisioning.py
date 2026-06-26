#!/usr/bin/env python3
"""CRUD de tenants (organizaciones SaaS EMAcción — no confundir con Apps de marketing)."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine import knowledge_api, tenant_profile
from Motor_Tecnico.accio_engine import tenant as tenant_mod
from Motor_Tecnico.accio_engine.tenant import (
    DEFAULT_TENANT,
    TenantNotFoundError,
    normalize_tenant_id,
    resolve_tenant,
)

_TENANT_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{1,48}$")
_PROTECTED_TENANTS = frozenset({DEFAULT_TENANT})

_DEFAULT_USERS = {
    "users": [
        {"id": "admin", "email": "", "role": "admin", "name": "Administrador", "active": True}
    ],
    "roles": [
        {"id": "admin", "label": "Administrador", "permissions": ["*"]},
        {"id": "operator", "label": "Operador", "permissions": ["read", "publish", "config"]},
        {"id": "viewer", "label": "Solo lectura", "permissions": ["read"]},
    ],
}

_MINIMAL_CONNECTORS = {
    "version": 1,
    "strategy": "Configurar conectores desde el dashboard",
    "connectors": [],
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _save_registry(data: dict[str, Any]) -> None:
    data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = tenant_mod.REGISTRY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_tenant_id(tenant_id: str) -> str:
    tid = (tenant_id or "").strip().lower()
    if not _TENANT_ID_RE.match(tid):
        raise ValueError(
            "ID inválido: use minúsculas, números, guión o guión bajo (2–49 caracteres, empieza con letra)"
        )
    return tid


def list_companies(*, include_disabled: bool = False) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw in tenant_mod.load_registry().get("tenants", []):
        status = raw.get("status", "active")
        if not include_disabled and status != "active":
            continue
        tid = raw["tenant_id"]
        ctx = {}
        ctx_path = tenant_mod.TENANTS_ROOT / tid / "business_context.json"
        if ctx_path.is_file():
            try:
                ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                ctx = {}
        items.append(
            {
                "tenant_id": tid,
                "display_name": raw.get("display_name", tid),
                "status": status,
                "crm_target": raw.get("crm_target", "odoo"),
                "timezone": raw.get("timezone", "America/Panama"),
                "default_locale": raw.get("default_locale", "es-PA"),
                "domains": list(raw.get("domains") or []),
                "created_at": raw.get("created_at"),
                "en1_organization_id": raw.get("en1_organization_id"),
                "en1_subdomain": raw.get("en1_subdomain"),
                "empresa": ctx.get("empresa") or raw.get("display_name", tid),
                "industria": ctx.get("industria", ""),
                "pais": ctx.get("pais", ""),
            }
        )
    return sorted(items, key=lambda r: r["display_name"].lower())


def get_company(tenant_id: str) -> dict[str, Any]:
    tid = validate_tenant_id(tenant_id)
    reg = tenant_mod.load_registry()
    record = next((r for r in reg.get("tenants", []) if r.get("tenant_id") == tid), None)
    if not record:
        raise TenantNotFoundError(f"Tenant no encontrado: {tid}")
    profile = tenant_profile.load_profile(tid)
    context = knowledge_api.load_business_context(tid)
    return {
        "tenant_id": tid,
        "display_name": record.get("display_name", tid),
        "status": record.get("status", "active"),
        "crm_target": record.get("crm_target", "odoo"),
        "timezone": record.get("timezone", profile.get("timezone", "America/Panama")),
        "default_locale": record.get("default_locale", "es-PA"),
        "domains": list(record.get("domains") or profile.get("domains") or []),
        "created_at": record.get("created_at") or profile.get("created_at"),
        "branding": profile.get("branding") or {},
        "context": context,
    }


def _bootstrap_files(tenant_id: str, record: dict[str, Any], context: dict[str, Any]) -> None:
    root = tenant_mod.TENANTS_ROOT / tenant_id
    root.mkdir(parents=True, exist_ok=True)
    (root / "knowledge").mkdir(parents=True, exist_ok=True)
    (root / "metrics").mkdir(parents=True, exist_ok=True)
    (root / "assets").mkdir(parents=True, exist_ok=True)

    now = _utc_now()
    profile = {
        "tenant_id": tenant_id,
        "display_name": record.get("display_name", tenant_id),
        "status": record.get("status", "active"),
        "crm_target": record.get("crm_target", "odoo"),
        "default_locale": record.get("default_locale", "es-PA"),
        "domains": list(record.get("domains") or []),
        "timezone": record.get("timezone", "America/Panama"),
        "created_at": record.get("created_at", now),
        "branding": dict(tenant_profile.DEFAULT_BRANDING),
    }
    _write_json(root / "tenant.json", profile)

    ctx = {
        "version": 1,
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
        "empresa": context.get("empresa") or record.get("display_name", tenant_id),
        "industria": context.get("industria", ""),
        "pais": context.get("pais", "Panamá"),
        "publico_objetivo": context.get("publico_objetivo", ""),
        "productos_servicios": context.get("productos_servicios") or [],
        "diferenciadores": context.get("diferenciadores") or [],
        "problemas_que_resuelve": context.get("problemas_que_resuelve") or [],
        "tono_comunicacion": context.get("tono_comunicacion", ""),
        "objetivos_comerciales": context.get("objetivos_comerciales") or [],
        "cta_principal": context.get("cta_principal", "DIAGNÓSTICO"),
        "contacto": context.get("contacto") or {},
    }
    _write_json(root / "business_context.json", ctx)

    users = json.loads(json.dumps(_DEFAULT_USERS))
    users["updated_at"] = now
    admin_email = context.get("admin_email") or f"admin@{tenant_id}.local"
    users["users"][0]["email"] = admin_email
    _write_json(root / "users.json", users)

    _write_json(root / "connectors.json", {**_MINIMAL_CONNECTORS, "updated_at": now[:10]})
    _write_json(root / "editorial_rules.json", {"version": 1, "target_matrix": {"valor": 75, "venta": 25}})
    _write_json(root / "content_queue.json", {"posts": []})
    _write_json(root / "calendar.json", {"updated_at": now[:10], "timezone": record.get("timezone", "America/Panama"), "weeks": []})
    _write_json(root / "campaigns.json", {"updated_at": now[:10], "campaigns": []})
    _write_json(root / "orders.json", {"orders": []})
    _write_json(root / "state.json", {"last_tick": None, "last_actions": {}})
    _write_json(root / "tasks.json", {"tasks": []})
    _write_json(root / "knowledge" / "manifest.json", {"version": 1, "articles": []})
    _write_json(
        root / "landings.json",
        {
            "base_domain": (record.get("domains") or [f"{tenant_id}.local"])[0],
            "default_utm_source": "emaccion",
            "landings": [],
            "updated_at": now,
        },
    )
    _write_json(
        root / "publication.json",
        {
            "default_channels": ["linkedin"],
            "auto_publish": False,
            "require_connection_test": True,
            "timezone": record.get("timezone", "America/Panama"),
            "updated_at": now,
        },
    )
    _write_json(
        root / "ai.json",
        {"topic_model": "rules", "image_model": "static_flyers", "tone_override": "", "enabled": True, "updated_at": now},
    )
    _write_json(root / "variables.json", {"version": 1, "variables": [], "updated_at": now})
    from Motor_Tecnico.accio_engine import marketing_app

    marketing_app.bootstrap_registry(tenant_id)


def create_company(payload: dict[str, Any]) -> dict[str, Any]:
    tid = validate_tenant_id(payload.get("tenant_id") or "")
    reg = tenant_mod.load_registry()
    if any(r.get("tenant_id") == tid for r in reg.get("tenants", [])):
        raise ValueError(f"Ya existe un tenant con ID «{tid}»")

    display_name = (payload.get("display_name") or payload.get("empresa") or tid).strip()
    if not display_name:
        raise ValueError("Nombre del tenant obligatorio")

    domains = payload.get("domains") or []
    if isinstance(domains, str):
        domains = [d.strip() for d in domains.split(",") if d.strip()]

    record = {
        "tenant_id": tid,
        "display_name": display_name,
        "status": "active",
        "default_locale": payload.get("default_locale") or "es-PA",
        "timezone": payload.get("timezone") or "America/Panama",
        "crm_target": (payload.get("crm_target") or "odoo").strip().lower(),
        "domains": domains,
        "created_at": _utc_now(),
    }
    context = payload.get("context") if isinstance(payload.get("context"), dict) else payload
    reg.setdefault("tenants", []).append(record)
    _save_registry(reg)
    _bootstrap_files(tid, record, context)
    branding = payload.get("branding")
    if isinstance(branding, dict) and branding:
        tenant_profile.save_profile(tid, {"branding": branding})
    return get_company(tid)


def update_company(tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    tid = validate_tenant_id(tenant_id)
    reg = tenant_mod.load_registry()
    record = next((r for r in reg.get("tenants", []) if r.get("tenant_id") == tid), None)
    if not record:
        raise TenantNotFoundError(f"Tenant no encontrado: {tid}")

    if "display_name" in payload and payload["display_name"]:
        record["display_name"] = str(payload["display_name"]).strip()
    for key in ("crm_target", "timezone", "default_locale", "status"):
        if key in payload and payload[key] is not None:
            record[key] = payload[key]
    if "domains" in payload:
        domains = payload["domains"]
        if isinstance(domains, str):
            domains = [d.strip() for d in domains.split(",") if d.strip()]
        record["domains"] = list(domains)

    _save_registry(reg)

    profile_payload: dict[str, Any] = {}
    if record.get("display_name"):
        profile_payload["display_name"] = record["display_name"]
    for key in ("timezone", "domains", "default_locale"):
        if key in record:
            profile_payload[key] = record[key]
    if profile_payload:
        tenant_profile.save_profile(tid, profile_payload)

    context = payload.get("context")
    if context is None and any(k in payload for k in ("empresa", "industria", "pais")):
        context = payload
    if isinstance(context, dict):
        knowledge_api.save_business_context(context, tid)

    branding = payload.get("branding")
    if isinstance(branding, dict) and branding:
        tenant_profile.save_profile(tid, {"branding": branding})

    return get_company(tid)


def disable_company(tenant_id: str) -> dict[str, Any]:
    tid = validate_tenant_id(tenant_id)
    if tid in _PROTECTED_TENANTS:
        raise ValueError(f"No se puede desactivar el tenant protegido «{tid}»")
    reg = tenant_mod.load_registry()
    record = next((r for r in reg.get("tenants", []) if r.get("tenant_id") == tid), None)
    if not record:
        raise TenantNotFoundError(f"Tenant no encontrado: {tid}")
    active = [r for r in reg.get("tenants", []) if r.get("status") == "active"]
    if len(active) <= 1 and record.get("status") == "active":
        raise ValueError("Debe quedar al menos un tenant activo")
    record["status"] = "disabled"
    _save_registry(reg)
    return {"tenant_id": tid, "status": "disabled"}


def enable_company(tenant_id: str) -> dict[str, Any]:
    tid = validate_tenant_id(tenant_id)
    reg = tenant_mod.load_registry()
    record = next((r for r in reg.get("tenants", []) if r.get("tenant_id") == tid), None)
    if not record:
        raise TenantNotFoundError(f"Tenant no encontrado: {tid}")
    record["status"] = "active"
    _save_registry(reg)
    tenant_profile.save_profile(tid, {"status": "active"})
    return {"tenant_id": tid, "status": "active"}


def delete_company(tenant_id: str, *, purge: bool = False) -> dict[str, Any]:
    """Baja lógica por defecto; purge=True elimina carpeta (solo no protegidos)."""
    tid = validate_tenant_id(tenant_id)
    if tid in _PROTECTED_TENANTS:
        raise ValueError(f"No se puede eliminar el tenant protegido «{tid}»")
    if purge:
        result = disable_company(tid)
        root = tenant_mod.TENANTS_ROOT / tid
        if root.is_dir():
            shutil.rmtree(root)
        reg = tenant_mod.load_registry()
        reg["tenants"] = [r for r in reg.get("tenants", []) if r.get("tenant_id") != tid]
        _save_registry(reg)
        return {**result, "purged": True}
    return disable_company(tid)
