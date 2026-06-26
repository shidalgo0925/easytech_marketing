#!/usr/bin/env python3
"""Fase N — almacén cifrado de credenciales por tenant."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRETS_DIR = BASE_DIR / "Marketing" / "tenants" / ".secrets"
DB_PATH = SECRETS_DIR / "tenant_secrets.db"
AUDIT_PATH = SECRETS_DIR / "settings_audit.log"

CONNECTOR_FIELDS: dict[str, list[dict[str, str]]] = {
    "linkedin": [
        {"key": "linkedin_client_id", "label": "LinkedIn Client ID", "secret": False},
        {"key": "linkedin_client_secret", "label": "LinkedIn Client Secret", "secret": True},
        {"key": "linkedin_access_token", "label": "LinkedIn Access Token", "secret": True},
        {"key": "linkedin_author_urn", "label": "LinkedIn Author URN", "secret": False},
    ],
    "meta": [
        {"key": "meta_app_id", "label": "Meta App ID", "secret": False},
        {"key": "meta_app_secret", "label": "Meta App Secret", "secret": True},
        {"key": "meta_page_id", "label": "Facebook Page ID", "secret": False},
        {"key": "meta_page_access_token", "label": "Facebook Page Token", "secret": True},
        {"key": "meta_ig_user_id", "label": "Instagram User ID", "secret": False},
    ],
    "google": [
        {"key": "google_client_id", "label": "Google Client ID", "secret": False},
        {"key": "google_client_secret", "label": "Google Client Secret", "secret": True},
        {"key": "google_oauth_refresh_token", "label": "Google Refresh Token", "secret": True},
    ],
    "tiktok": [
        {"key": "tiktok_client_key", "label": "TikTok Client Key", "secret": False},
        {"key": "tiktok_client_secret", "label": "TikTok Client Secret", "secret": True},
        {"key": "tiktok_access_token", "label": "TikTok Access Token", "secret": True},
    ],
}

CRM_FIELDS: list[dict[str, str]] = [
    {"key": "en1_api_url", "label": "EN1 API URL", "secret": False},
    {"key": "en1_api_key", "label": "EN1 API Key", "secret": True},
    {"key": "odoo_url", "label": "Odoo URL", "secret": False},
    {"key": "odoo_db", "label": "Odoo DB", "secret": False},
    {"key": "odoo_user", "label": "Odoo Usuario", "secret": False},
    {"key": "odoo_password", "label": "Odoo API Key / Password", "secret": True},
]

PLATFORM_FIELDS: list[dict[str, str]] = [
    {"key": "accio_api_key", "label": "API Key dashboard (tenant)", "secret": True},
]

VARIABLE_FIELDS: list[dict[str, str]] = [
    {"key": "webhook_url", "label": "Webhook URL", "secret": False},
    {"key": "webhook_secret", "label": "Webhook Secret", "secret": True},
    {"key": "openai_api_key", "label": "OpenAI API Key (IA)", "secret": True},
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fernet() -> Fernet:
    raw = os.getenv("ACCIO_SECRETS_KEY", "").strip() or os.getenv("ACCIO_API_KEY", "accio-default-secrets")
    digest = hashlib.sha256(raw.encode()).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def _ensure_db() -> None:
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tenant_secrets (
                tenant_id TEXT NOT NULL,
                namespace TEXT NOT NULL,
                key TEXT NOT NULL,
                value_encrypted TEXT NOT NULL,
                validation_status TEXT DEFAULT 'pending',
                validated_at TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (tenant_id, namespace, key)
            )
            """
        )
        conn.commit()


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "••••"
    return "••••••••" + value[-4:]


def _audit(tenant_id: str, actor: str, section: str, field: str, action: str, success: bool) -> None:
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {
            "at": _utc_now(),
            "tenant_id": tenant_id,
            "actor": actor,
            "section": section,
            "field": field,
            "action": action,
            "success": success,
        },
        ensure_ascii=False,
    )
    with AUDIT_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def set_secret(
    tenant_id: str,
    namespace: str,
    key: str,
    value: str,
    *,
    actor: str = "dashboard",
    reset_validation: bool = True,
) -> None:
    _ensure_db()
    f = _fernet()
    enc = f.encrypt(value.encode()).decode()
    status = "pending" if reset_validation else None
    now = _utc_now()
    with sqlite3.connect(DB_PATH) as conn:
        if reset_validation:
            conn.execute(
                """
                INSERT INTO tenant_secrets (tenant_id, namespace, key, value_encrypted, validation_status, validated_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', NULL, ?)
                ON CONFLICT(tenant_id, namespace, key) DO UPDATE SET
                    value_encrypted=excluded.value_encrypted,
                    validation_status='pending',
                    validated_at=NULL,
                    updated_at=excluded.updated_at
                """,
                (tenant_id, namespace, key, enc, now),
            )
        else:
            conn.execute(
                """
                INSERT INTO tenant_secrets (tenant_id, namespace, key, value_encrypted, validation_status, validated_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', NULL, ?)
                ON CONFLICT(tenant_id, namespace, key) DO UPDATE SET
                    value_encrypted=excluded.value_encrypted,
                    updated_at=excluded.updated_at
                """,
                (tenant_id, namespace, key, enc, now),
            )
        conn.commit()
    _audit(tenant_id, actor, namespace, key, "set", True)


def get_secret(tenant_id: str, namespace: str, key: str) -> str | None:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT value_encrypted FROM tenant_secrets WHERE tenant_id=? AND namespace=? AND key=?",
            (tenant_id, namespace, key),
        ).fetchone()
    if not row:
        return _env_fallback(tenant_id, key)
    try:
        return _fernet().decrypt(row[0].encode()).decode()
    except InvalidToken:
        return None


def get_validation_status(tenant_id: str, namespace: str, key: str) -> str:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT validation_status FROM tenant_secrets WHERE tenant_id=? AND namespace=? AND key=?",
            (tenant_id, namespace, key),
        ).fetchone()
    return row[0] if row else "unset"


def set_validation(tenant_id: str, namespace: str, key: str, status: str) -> None:
    _ensure_db()
    now = _utc_now()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE tenant_secrets SET validation_status=?, validated_at=?, updated_at=?
            WHERE tenant_id=? AND namespace=? AND key=?
            """,
            (status, now if status == "active" else None, now, tenant_id, namespace, key),
        )
        conn.commit()


def _env_fallback(tenant_id: str, key: str) -> str | None:
    """Solo easytech hereda .env global durante transición."""
    if tenant_id != "easytech":
        return None
    env_key = key.upper()
    val = os.getenv(env_key, "").strip()
    return val or None


def connector_env_value(tenant_id: str, env_key: str) -> str:
    """Valor para publishers: secretos validados > .env (easytech)."""
    val = get_secret(tenant_id, "connectors", env_key.lower())
    if val:
        if get_validation_status(tenant_id, "connectors", env_key.lower()) == "active":
            return val
        # credencial guardada pero no validada — no usar en publish
        return ""
    return os.getenv(env_key.upper(), "").strip() if tenant_id == "easytech" else ""


def list_namespace(tenant_id: str, namespace: str, fields: list[dict[str, str]]) -> list[dict[str, Any]]:
    items = []
    for field in fields:
        key = field["key"]
        stored = get_secret(tenant_id, namespace, key)
        status = get_validation_status(tenant_id, namespace, key)
        if stored and status == "unset" and tenant_id == "easytech" and _env_fallback(tenant_id, key):
            status = "active"  # heredado de .env
        items.append(
            {
                "key": key,
                "label": field["label"],
                "secret": field.get("secret", True),
                "configured": bool(stored),
                "masked": _mask(stored or ""),
                "validation_status": status if stored else "unset",
            }
        )
    return items


def get_settings_view(tenant_id: str) -> dict[str, Any]:
    from Motor_Tecnico.accio_engine.tenant import resolve_tenant

    tenant = resolve_tenant(tenant_id)
    return {
        "tenant_id": tenant.tenant_id,
        "display_name": tenant.display_name,
        "crm_target": tenant.crm_target,
        "connectors": {
            "linkedin": list_namespace(tenant_id, "connectors", CONNECTOR_FIELDS["linkedin"]),
            "meta": list_namespace(tenant_id, "connectors", CONNECTOR_FIELDS["meta"]),
            "google": list_namespace(tenant_id, "connectors", CONNECTOR_FIELDS["google"]),
            "tiktok": list_namespace(tenant_id, "connectors", CONNECTOR_FIELDS["tiktok"]),
        },
        "crm": list_namespace(tenant_id, "crm", CRM_FIELDS),
        "platform": list_namespace(tenant_id, "platform", PLATFORM_FIELDS),
        "variables_secret": list_namespace(tenant_id, "variables", VARIABLE_FIELDS),
    }


def save_settings_section(
    tenant_id: str,
    namespace: str,
    payload: dict[str, Any],
    *,
    actor: str = "dashboard",
) -> dict[str, Any]:
    field_map: dict[str, list[dict[str, str]]] = {
        "connectors": [f for group in CONNECTOR_FIELDS.values() for f in group],
        "crm": CRM_FIELDS,
        "platform": PLATFORM_FIELDS,
        "variables": VARIABLE_FIELDS,
    }
    allowed_keys = {f["key"] for f in field_map.get(namespace, [])}
    for key, value in payload.items():
        if key not in allowed_keys:
            continue
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        set_secret(tenant_id, namespace, key, str(value).strip(), actor=actor)
    return get_settings_view(tenant_id)


def test_connector(tenant_id: str, connector_id: str) -> dict[str, Any]:
    import requests

    connector_id = connector_id.lower()
    try:
        if connector_id == "linkedin":
            token = get_secret(tenant_id, "connectors", "linkedin_access_token") or _env_fallback(tenant_id, "linkedin_access_token")
            if not token:
                return {"ok": False, "error": "Falta linkedin_access_token"}
            r = requests.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            ok = r.status_code == 200
            if ok:
                for key in ("linkedin_access_token",):
                    if get_secret(tenant_id, "connectors", key) or tenant_id == "easytech":
                        set_validation(tenant_id, "connectors", key, "active")
            return {"ok": ok, "status_code": r.status_code, "detail": r.text[:200]}

        if connector_id in ("meta", "facebook", "instagram"):
            token = get_secret(tenant_id, "connectors", "meta_page_access_token") or _env_fallback(tenant_id, "meta_page_access_token")
            if not token:
                return {"ok": False, "error": "Falta meta_page_access_token"}
            r = requests.get(
                "https://graph.facebook.com/v19.0/me",
                params={"access_token": token},
                timeout=15,
            )
            ok = r.status_code == 200 and "id" in r.json()
            if ok:
                set_validation(tenant_id, "connectors", "meta_page_access_token", "active")
            return {"ok": ok, "status_code": r.status_code, "detail": r.text[:200]}

        if connector_id == "google":
            token = get_secret(tenant_id, "connectors", "google_oauth_refresh_token") or _env_fallback(tenant_id, "google_oauth_refresh_token")
            if not token:
                return {"ok": False, "error": "Falta google_oauth_refresh_token"}
            set_validation(tenant_id, "connectors", "google_oauth_refresh_token", "active")
            return {"ok": True, "detail": "Token presente (validación completa requiere OAuth flow)"}

        if connector_id == "tiktok":
            token = get_secret(tenant_id, "connectors", "tiktok_access_token") or _env_fallback(tenant_id, "tiktok_access_token")
            if not token:
                return {"ok": False, "error": "Falta tiktok_access_token"}
            set_validation(tenant_id, "connectors", "tiktok_access_token", "active")
            return {"ok": True, "detail": "Token presente"}

        return {"ok": False, "error": f"Conector desconocido: {connector_id}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def test_crm(tenant_id: str) -> dict[str, Any]:
    import xmlrpc.client

    from Motor_Tecnico.accio_engine.tenant import resolve_tenant

    tenant = resolve_tenant(tenant_id)
    if tenant.crm_target == "en1":
        url = get_secret(tenant_id, "crm", "en1_api_url")
        key = get_secret(tenant_id, "crm", "en1_api_key")
        if not url:
            return {"ok": False, "error": "Falta en1_api_url"}
        return {"ok": True, "detail": "EN1 URL configurada (health check pendiente de API EN1)"}

    url = get_secret(tenant_id, "crm", "odoo_url") or _env_fallback(tenant_id, "odoo_url")
    db = get_secret(tenant_id, "crm", "odoo_db") or _env_fallback(tenant_id, "odoo_db")
    user = get_secret(tenant_id, "crm", "odoo_user") or _env_fallback(tenant_id, "odoo_user")
    password = get_secret(tenant_id, "crm", "odoo_password") or _env_fallback(tenant_id, "odoo_password")
    if not all([url, db, user, password]):
        return {"ok": False, "error": "Faltan campos Odoo"}
    try:
        common = xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/common", allow_none=True)
        uid = common.authenticate(db, user, password, {})
        ok = bool(uid)
        if ok:
            for key in ("odoo_url", "odoo_db", "odoo_user", "odoo_password"):
                if get_secret(tenant_id, "crm", key):
                    set_validation(tenant_id, "crm", key, "active")
        return {"ok": ok, "uid": uid}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def import_env_to_tenant(tenant_id: str = "easytech") -> int:
    """Migra secretos del .env global al almacén del tenant (una vez)."""
    connector_keys = {f["key"] for group in CONNECTOR_FIELDS.values() for f in group}
    crm_keys = {f["key"] for f in CRM_FIELDS}
    variable_keys = {f["key"] for f in VARIABLE_FIELDS}
    count = 0
    for field in [f for group in CONNECTOR_FIELDS.values() for f in group] + CRM_FIELDS + PLATFORM_FIELDS + VARIABLE_FIELDS:
        key = field["key"]
        val = os.getenv(key.upper(), "").strip()
        if not val:
            continue
        if key in connector_keys:
            ns = "connectors"
        elif key in crm_keys:
            ns = "crm"
        elif key in variable_keys:
            ns = "variables"
        else:
            ns = "platform"
        set_secret(tenant_id, ns, key, val, actor="import_env", reset_validation=False)
        set_validation(tenant_id, ns, key, "active")
        count += 1
    return count
