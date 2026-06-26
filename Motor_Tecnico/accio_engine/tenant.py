#!/usr/bin/env python3
"""Fase M — modelo tenant y rutas de datos por cliente."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TENANTS_ROOT = BASE_DIR / "Marketing" / "tenants"
REGISTRY_PATH = TENANTS_ROOT / "registry.json"
DEFAULT_TENANT = "easytech"
_TENANT_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{1,48}$")

# Rutas legacy (pre multi-tenant) — solo fallback easytech
LEGACY_ACCIO = BASE_DIR / "Marketing" / "accio"
LEGACY_KNOWLEDGE = BASE_DIR / "Marketing" / "knowledge"
LEGACY_QUEUE = BASE_DIR / "Marketing" / "content_queue.json"


class TenantNotFoundError(KeyError):
    pass


@dataclass(frozen=True)
class Tenant:
    tenant_id: str
    display_name: str
    status: str
    root: Path
    crm_target: str = "odoo"
    default_locale: str = "es-PA"
    timezone: str = "America/Panama"
    domains: tuple[str, ...] = ()
    subdomain: str | None = None
    registration: str = "open"
    created_at: str | None = None

    @property
    def business_context_path(self) -> Path:
        return self.root / "business_context.json"

    @property
    def editorial_rules_path(self) -> Path:
        return self.root / "editorial_rules.json"

    @property
    def content_queue_path(self) -> Path:
        return self.root / "content_queue.json"

    @property
    def campaigns_path(self) -> Path:
        return self.root / "campaigns.json"

    @property
    def calendar_path(self) -> Path:
        return self.root / "calendar.json"

    @property
    def connectors_path(self) -> Path:
        return self.root / "connectors.json"

    @property
    def orders_path(self) -> Path:
        return self.root / "orders.json"

    @property
    def state_path(self) -> Path:
        return self.root / "state.json"

    @property
    def tasks_path(self) -> Path:
        return self.root / "tasks.json"

    @property
    def knowledge_dir(self) -> Path:
        return self.root / "knowledge"

    @property
    def knowledge_manifest_path(self) -> Path:
        return self.knowledge_dir / "manifest.json"

    @property
    def metrics_dir(self) -> Path:
        return self.root / "metrics"

    @property
    def publish_log_path(self) -> Path:
        return self.root / "publish_log.json"

    @property
    def meta_publish_log_path(self) -> Path:
        return self.root / "meta_publish_log.json"

    @property
    def flyers_dir(self) -> Path:
        shared = BASE_DIR / "Marketing" / "flyers"
        local = self.root / "flyers"
        return local if local.is_dir() else shared

    @property
    def flyers_manifest_path(self) -> Path:
        return self.flyers_dir / "manifest.json"

    def ensure_dirs(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.is_file():
        return {"version": 1, "tenants": []}
    return _read_json(REGISTRY_PATH)


def list_tenants(active_only: bool = True) -> list[Tenant]:
    reg = load_registry()
    items: list[Tenant] = []
    for raw in reg.get("tenants", []):
        if active_only and raw.get("status") != "active":
            continue
        items.append(_tenant_from_record(raw))
    return items


def _tenant_from_record(raw: dict[str, Any]) -> Tenant:
    tid = raw["tenant_id"]
    return Tenant(
        tenant_id=tid,
        display_name=raw.get("display_name", tid),
        status=raw.get("status", "active"),
        root=TENANTS_ROOT / tid,
        crm_target=raw.get("crm_target", "odoo"),
        default_locale=raw.get("default_locale", "es-PA"),
        timezone=raw.get("timezone", "America/Panama"),
        domains=tuple(raw.get("domains") or ()),
        subdomain=raw.get("subdomain"),
        registration=raw.get("registration", "open"),
        created_at=raw.get("created_at"),
    )


def normalize_tenant_id(tenant_id: str | None) -> str:
    tid = (tenant_id or DEFAULT_TENANT).strip().lower()
    if not _TENANT_ID_RE.match(tid):
        raise TenantNotFoundError(f"tenant_id inválido: {tenant_id}")
    return tid


def resolve_tenant(tenant_id: str | None = None) -> Tenant:
    tid = normalize_tenant_id(tenant_id)
    for raw in load_registry().get("tenants", []):
        if raw.get("tenant_id") == tid:
            if raw.get("status") == "disabled":
                raise TenantNotFoundError(f"Tenant deshabilitado: {tid}")
            tenant = _tenant_from_record(raw)
            tenant.ensure_dirs()
            return tenant
    raise TenantNotFoundError(f"Tenant no encontrado: {tid}")


def legacy_paths_for(tenant: Tenant) -> Tenant:
    """Si el tenant aún no tiene datos migrados, usa rutas legacy (solo easytech)."""
    if tenant.tenant_id != DEFAULT_TENANT:
        return tenant
    if tenant.content_queue_path.is_file():
        return tenant
    # Fallback transparente pre-migración
    return Tenant(
        tenant_id=tenant.tenant_id,
        display_name=tenant.display_name,
        status=tenant.status,
        root=LEGACY_ACCIO.parent / "tenants" / tenant.tenant_id,
        crm_target=tenant.crm_target,
        default_locale=tenant.default_locale,
        timezone=tenant.timezone,
        domains=tenant.domains,
        created_at=tenant.created_at,
    )


def effective_paths(tenant: Tenant) -> dict[str, Path]:
    """Devuelve paths efectivos con fallback legacy para easytech."""
    t = resolve_tenant(tenant.tenant_id)
    if t.tenant_id == DEFAULT_TENANT and not t.content_queue_path.is_file() and LEGACY_QUEUE.is_file():
        return {
            "content_queue": LEGACY_QUEUE,
            "calendar": LEGACY_ACCIO / "calendar.json",
            "campaigns": LEGACY_ACCIO / "campaigns.json",
            "connectors": LEGACY_ACCIO / "connectors.json",
            "orders": LEGACY_ACCIO / "orders.json",
            "state": LEGACY_ACCIO / "state.json",
            "tasks": LEGACY_ACCIO / "tasks.json",
            "business_context": LEGACY_ACCIO / "business_context.json",
            "editorial_rules": LEGACY_ACCIO / "editorial_rules.json",
            "knowledge_dir": LEGACY_KNOWLEDGE,
            "knowledge_manifest": LEGACY_KNOWLEDGE / "manifest.json",
            "flyers_dir": BASE_DIR / "Marketing" / "flyers",
            "flyers_manifest": BASE_DIR / "Marketing" / "flyers" / "manifest.json",
            "publish_log": BASE_DIR / "Marketing" / "publish_log.json",
            "meta_publish_log": BASE_DIR / "Marketing" / "meta_publish_log.json",
        }
    return {
        "content_queue": t.content_queue_path,
        "calendar": t.calendar_path,
        "campaigns": t.campaigns_path,
        "connectors": t.connectors_path,
        "orders": t.orders_path,
        "state": t.state_path,
        "tasks": t.tasks_path,
        "business_context": t.business_context_path,
        "editorial_rules": t.editorial_rules_path,
        "knowledge_dir": t.knowledge_dir,
        "knowledge_manifest": t.knowledge_manifest_path,
        "flyers_dir": t.flyers_dir,
        "flyers_manifest": t.flyers_manifest_path,
        "publish_log": t.publish_log_path,
        "meta_publish_log": t.meta_publish_log_path,
    }
