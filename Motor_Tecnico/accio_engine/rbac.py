#!/usr/bin/env python3
"""RBAC por tenant — Fase C V2."""

from __future__ import annotations

import re
from typing import Any

from Motor_Tecnico.accio_engine import auth_service, settings_center

ALL_PERMISSIONS = frozenset({"read", "publish", "config", "admin", "platform"})


def role_permissions(tenant_id: str) -> dict[str, set[str]]:
    roles = settings_center.load_users(tenant_id).get("roles", [])
    out: dict[str, set[str]] = {}
    for row in roles:
        raw = row.get("permissions") or []
        if "*" in raw:
            out[row["id"]] = set(ALL_PERMISSIONS)
        else:
            out[row["id"]] = {p for p in raw if p in ALL_PERMISSIONS}
    return out


def has_permission(role_id: str, permission: str, tenant_id: str) -> bool:
    if permission not in ALL_PERMISSIONS:
        return False
    if auth_service.has_permission(role_id, permission):
        return True
    perms = role_permissions(tenant_id).get(role_id, set())
    if "*" in perms or perms == set(ALL_PERMISSIONS):
        return True
    return permission in perms


def permission_for_request(method: str, path: str, tenant_id: str) -> str | None:
    if method == "GET" or method == "HEAD":
        return "read"
    marker = f"/accio/{tenant_id}/"
    rel = path.split(marker, 1)[-1] if marker in path else path.removeprefix("/accio/")
    rel = rel.lstrip("/")
    if rel.startswith("settings/backup") or rel.startswith("settings/usuarios"):
        return "admin"
    if rel.startswith("settings/empresas"):
        if method != "GET" and (rel.endswith("/disable") or rel.endswith("/enable")):
            return "platform"
        if method == "POST" and rel.rstrip("/") == "settings/empresas":
            return "platform"
        return "admin"
    if rel.startswith("settings/platform") or rel.startswith("settings/logo"):
        return "admin"
    if rel.startswith("run/") or rel == "tick":
        return "publish"
    if rel.startswith("orders"):
        return "publish"
    if rel.startswith("content/queue") or rel.startswith("content/generate-topic"):
        return "publish"
    if rel.startswith("settings/"):
        return "config"
    if rel.startswith("config/") or rel.startswith("calendar"):
        return "config"
    return "config"


def sanitize_users_for_api(data: dict[str, Any]) -> dict[str, Any]:
    users = []
    for row in data.get("users", []):
        users.append({k: v for k, v in row.items() if k not in ("password_hash", "password")})
    return {**data, "users": users}
