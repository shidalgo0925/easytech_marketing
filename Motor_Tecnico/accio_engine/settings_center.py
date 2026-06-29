#!/usr/bin/env python3
"""Fase C V2 — Configuration Center (datos no secretos por tenant)."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

from Motor_Tecnico.accio_engine import knowledge_api, rbac, tenant_profile, tenant_secrets
from Motor_Tecnico.accio_engine.tenant import resolve_tenant

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"
BACKUP_SCRIPT = BASE_DIR / "scripts" / "backup_secrets.sh"

PRODUCT_SLUG_RE = re.compile(r"^[a-z][a-z0-9_-]{1,48}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _path(tenant_id: str, name: str) -> Path:
    return resolve_tenant(tenant_id).root / name


def _read_json(path: Path, default: dict | list) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _default_products(tenant_id: str) -> dict[str, Any]:
    ctx = knowledge_api.load_business_context(tenant_id)
    items = []
    for i, name in enumerate(ctx.get("productos_servicios") or [], 1):
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower())[:40].strip("_") or f"product_{i}"
        items.append(
            {
                "slug": slug,
                "name": name,
                "enabled": True,
                "landing_path": "",
                "cta": ctx.get("cta_principal", "DIAGNÓSTICO"),
            }
        )
    return {"version": 1, "products": items}


def load_products(tenant_id: str) -> dict[str, Any]:
    from Motor_Tecnico.accio_engine.product_infrastructure.facade import (
        load_products as facade_load,
        product_store_active,
        save_products as facade_save,
    )

    if product_store_active():
        data = facade_load(tenant_id)
        if not data.get("products"):
            data = _default_products(tenant_id)
            facade_save(tenant_id, data)
        return data

    path = _path(tenant_id, "products.json")
    data = _read_json(path, None)
    if not data:
        data = _default_products(tenant_id)
        _write_json(path, data)
    return data


def save_products(tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    current = load_products(tenant_id)
    products = payload.get("products", payload if isinstance(payload, list) else None)
    if products is None:
        products = current.get("products", [])
    cleaned = []
    for p in products:
        slug = (p.get("slug") or "").strip().lower()
        if not PRODUCT_SLUG_RE.match(slug):
            raise ValueError(f"Slug de producto inválido: {slug}")
        cleaned.append(
            {
                "slug": slug,
                "name": (p.get("name") or slug).strip(),
                "enabled": bool(p.get("enabled", True)),
                "landing_path": (p.get("landing_path") or "").strip(),
                "cta": (p.get("cta") or "DIAGNÓSTICO").strip(),
                "hashtags": p.get("hashtags") or [],
            }
        )
    data = {"version": 1, "updated_at": _utc_now(), "products": cleaned}
    from Motor_Tecnico.accio_engine.product_infrastructure.facade import (
        product_store_active,
        save_products as facade_save,
    )

    if product_store_active():
        return facade_save(tenant_id, data)
    _write_json(_path(tenant_id, "products.json"), data)
    return data


def load_variables(tenant_id: str) -> dict[str, Any]:
    plain = _read_json(_path(tenant_id, "variables.json"), {"variables": []})
    secret_view = tenant_secrets.list_namespace(
        tenant_id, "variables", tenant_secrets.VARIABLE_FIELDS
    )
    return {"plain": plain.get("variables", []), "secret": secret_view}


def save_variables(tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    plain_vars = payload.get("plain") or []
    _write_json(
        _path(tenant_id, "variables.json"),
        {"version": 1, "updated_at": _utc_now(), "variables": plain_vars},
    )
    secrets = payload.get("secrets") or {}
    if secrets:
        tenant_secrets.save_settings_section(tenant_id, "variables", secrets)
    return load_variables(tenant_id)


def load_publication(tenant_id: str) -> dict[str, Any]:
    pub = _read_json(
        _path(tenant_id, "publication.json"),
        {
            "default_channels": ["linkedin", "facebook"],
            "auto_publish": False,
            "require_connection_test": True,
            "timezone": "America/Panama",
        },
    )
    pub["editorial_rules"] = knowledge_api.load_editorial_rules(tenant_id)
    return pub


def save_publication(tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    current = load_publication(tenant_id)
    for key in ("default_channels", "auto_publish", "require_connection_test", "timezone"):
        if key in payload:
            current[key] = payload[key]
    current["updated_at"] = _utc_now()
    rules = payload.get("editorial_rules")
    if rules:
        path = resolve_tenant(tenant_id).editorial_rules_path
        rules["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        _write_json(path, rules)
    _write_json(_path(tenant_id, "publication.json"), {k: v for k, v in current.items() if k != "editorial_rules"})
    return load_publication(tenant_id)


def load_landings(tenant_id: str) -> dict[str, Any]:
    return _read_json(
        _path(tenant_id, "landings.json"),
        {
            "base_domain": "easytech.services",
            "default_utm_source": "emaccion",
            "landings": [],
        },
    )


def save_landings(tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = load_landings(tenant_id)
    for key in ("base_domain", "default_utm_source", "landings"):
        if key in payload:
            data[key] = payload[key]
    data["updated_at"] = _utc_now()
    _write_json(_path(tenant_id, "landings.json"), data)
    return data


def load_ai_config(tenant_id: str) -> dict[str, Any]:
    return _read_json(
        _path(tenant_id, "ai.json"),
        {
            "topic_model": "llm",
            "image_model": "static_flyers",
            "tone_override": "",
            "enabled": True,
        },
    )


def save_ai_config(tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = load_ai_config(tenant_id)
    for key in ("topic_model", "image_model", "tone_override", "enabled"):
        if key in payload:
            data[key] = payload[key]
    data["updated_at"] = _utc_now()
    _write_json(_path(tenant_id, "ai.json"), data)
    return data


DEFAULT_ROLES: list[dict[str, Any]] = [
    {"id": "tenant_admin", "label": "Administrador del tenant", "permissions": ["*"]},
    {"id": "marketing_operator", "label": "Operador de marketing", "permissions": ["read", "publish"]},
    {"id": "viewer", "label": "Solo lectura", "permissions": ["read"]},
]


def _load_roles(tenant_id: str) -> list[dict[str, Any]]:
    data = _read_json(_path(tenant_id, "users.json"), {})
    roles = data.get("roles") or []
    if not roles:
        return list(DEFAULT_ROLES)
    return roles


def load_users(tenant_id: str) -> dict[str, Any]:
    from Motor_Tecnico.accio_engine import auth_service

    auth_service.migrate_from_tenant_json()
    users = auth_service.list_tenant_users(tenant_id)
    if not users:
        legacy = _read_json(_path(tenant_id, "users.json"), {})
        if legacy.get("users"):
            auth_service.migrate_from_tenant_json()
            users = auth_service.list_tenant_users(tenant_id)
    return {"users": users, "roles": _load_roles(tenant_id)}


def save_users(
    tenant_id: str,
    payload: dict[str, Any],
    *,
    actor_is_platform: bool = False,
) -> dict[str, Any]:
    from Motor_Tecnico.accio_engine import auth_service

    roles = payload.get("roles")
    if roles is not None:
        cleaned_roles = []
        for row in roles:
            rid = (row.get("id") or "").strip()
            if not rid:
                continue
            if not actor_is_platform and rid in auth_service.FORBIDDEN_CUSTOM_ROLE_IDS:
                raise ValueError(f"Rol «{rid}» reservado de plataforma")
            perms = row.get("permissions") or []
            if isinstance(perms, str):
                perms = [p.strip() for p in perms.split(",") if p.strip()]
            if not actor_is_platform and "platform" in perms:
                raise ValueError("Permiso «platform» reservado del super administrador")
            cleaned_roles.append(
                {
                    "id": rid,
                    "label": (row.get("label") or rid).strip(),
                    "permissions": perms,
                }
            )
        roles = cleaned_roles or list(DEFAULT_ROLES)
    else:
        roles = _load_roles(tenant_id)

    if "users" in payload:
        auth_service.sync_tenant_users(
            tenant_id,
            payload["users"],
            actor_is_platform=actor_is_platform,
        )
    users = auth_service.list_tenant_users(tenant_id)
    data = {"users": users, "roles": roles, "updated_at": _utc_now()}
    _write_json(_path(tenant_id, "users.json"), data)
    return rbac.sanitize_users_for_api(data)


def ensure_bootstrap_users(tenant_id: str, password: str) -> dict[str, Any] | None:
    """Crea usuario admin si el tenant no tiene ninguna contraseña configurada."""
    password = (password or "").strip()
    if not password:
        return None
    data = load_users(tenant_id)
    if any(u.get("password_hash") for u in data.get("users", [])):
        return None
    email = f"admin@{tenant_id}.local" if tenant_id != "easytech" else "admin@easytech.services"
    data["users"] = [
        {
            "id": "admin",
            "email": email,
            "role": "admin",
            "name": "Administrador",
            "active": True,
            "password_hash": generate_password_hash(password),
        }
    ]
    data["updated_at"] = _utc_now()
    _write_json(_path(tenant_id, "users.json"), data)
    return rbac.sanitize_users_for_api(data)


def bootstrap_all_tenants(password: str) -> list[str]:
    from Motor_Tecnico.accio_engine.tenant import list_tenants

    created: list[str] = []
    for tenant in list_tenants():
        if ensure_bootstrap_users(tenant.tenant_id, password):
            created.append(tenant.tenant_id)
    return created


def verify_user_login(tenant_id: str, login: str, password: str) -> dict[str, Any] | None:
    from Motor_Tecnico.accio_engine import auth_service

    user = auth_service.authenticate(login, password, tenant_id)
    if user:
        return {
            "user_id": user["user_id"],
            "role": user["role"],
            "name": user["name"],
        }
    login_norm = (login or "").strip().lower()
    password = password or ""
    if not login_norm or not password:
        return None
    for user in _read_json(_path(tenant_id, "users.json"), {}).get("users", []):
        if not user.get("active", True):
            continue
        email = (user.get("email") or "").strip().lower()
        uid = (user.get("id") or "").strip().lower()
        if login_norm not in (email, uid):
            continue
        if login_norm == email and not email:
            continue
        ph = user.get("password_hash")
        if ph and check_password_hash(ph, password):
            return {
                "user_id": user["id"],
                "role": user.get("role", "viewer"),
                "name": user.get("name") or user["id"],
            }
    return None


LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".webp"}


def save_tenant_logo(tenant_id: str, file_storage) -> str:
    from Motor_Tecnico.accio_engine.tenant import resolve_tenant

    ext = Path(file_storage.filename or "").suffix.lower()
    if ext not in LOGO_EXTENSIONS:
        raise ValueError("Formato de logo no permitido (png, jpg, svg, webp)")
    assets = resolve_tenant(tenant_id).root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    dest = assets / f"logo{ext}"
    file_storage.save(dest)
    url = f"/accio/{tenant_id}/assets/logo{ext}"
    tenant_profile.save_profile(tenant_id, {"branding": {"logo_url": url}})
    return url


def load_empresa(tenant_id: str, *, allowed_company_ids: set[str] | None = None) -> dict[str, Any]:
    from Motor_Tecnico.accio_engine import tenant_provisioning

    companies = tenant_provisioning.list_companies(include_disabled=True)
    if allowed_company_ids is not None:
        companies = [c for c in companies if c["tenant_id"] in allowed_company_ids]
    return {
        "context": knowledge_api.load_business_context(tenant_id),
        "companies": companies,
        "selected_tenant_id": tenant_id,
    }


def save_empresa(tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    ctx = payload.get("context", payload)
    saved = knowledge_api.save_business_context(ctx, tenant_id)
    return {"context": saved}


def read_audit_log(tenant_id: str, limit: int = 50) -> list[dict[str, Any]]:
    path = tenant_secrets.AUDIT_PATH
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    items = []
    for line in reversed(lines):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("tenant_id") not in (tenant_id, None):
            continue
        items.append(row)
        if len(items) >= limit:
            break
    return items


def read_logs(log_name: str = "accio_tick", lines: int = 80) -> dict[str, Any]:
    allowed = {
        "accio_tick": LOGS_DIR / "accio_tick.log",
        "cron": LOGS_DIR / "cron.log",
    }
    path = allowed.get(log_name)
    if not path or not path.is_file():
        return {"ok": False, "error": "Log no disponible", "lines": []}
    content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return {"ok": True, "log": log_name, "lines": content[-lines:]}


def run_backup() -> dict[str, Any]:
    if not BACKUP_SCRIPT.is_file():
        return {"ok": False, "error": "Script de backup no encontrado"}
    try:
        proc = subprocess.run(
            ["bash", str(BACKUP_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR),
            timeout=120,
        )
        return {
            "ok": proc.returncode == 0,
            "stdout": (proc.stdout or "")[-2000:],
            "stderr": (proc.stderr or "")[-1000:],
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def get_center_view(tenant_id: str, *, allowed_company_ids: set[str] | None = None) -> dict[str, Any]:
    tenant = resolve_tenant(tenant_id)
    secrets = tenant_secrets.get_settings_view(tenant_id)
    return {
        "tenant_id": tenant_id,
        "menu": [
            "empresa",
            "tenant",
            "usuarios",
            "productos",
            "conectores",
            "crm",
            "landing",
            "publicacion",
            "variables",
            "ia",
            "logs",
            "backups",
            "seguridad",
        ],
        "tenant_organization": load_empresa(tenant_id, allowed_company_ids=allowed_company_ids),
        "empresa": load_empresa(tenant_id, allowed_company_ids=allowed_company_ids),
        "tenant": tenant_profile.load_profile(tenant_id),
        "usuarios": rbac.sanitize_users_for_api(load_users(tenant_id)),
        "productos": load_products(tenant_id),
        "conectores": secrets.get("connectors"),
        "crm": secrets.get("crm"),
        "platform": secrets.get("platform"),
        "crm_target": tenant.crm_target,
        "landing": load_landings(tenant_id),
        "publicacion": load_publication(tenant_id),
        "variables": load_variables(tenant_id),
        "ia": load_ai_config(tenant_id),
        "seguridad": {
            "audit": read_audit_log(tenant_id, limit=30),
            "secrets_encrypted": True,
        },
    }
