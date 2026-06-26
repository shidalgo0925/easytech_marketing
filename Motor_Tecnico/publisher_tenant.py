#!/usr/bin/env python3
"""Contexto multi-tenant para publishers (credenciales + rutas por tenant)."""

from __future__ import annotations

import sys
from pathlib import Path

from Motor_Tecnico.accio_engine.tenant import DEFAULT_TENANT, effective_paths, resolve_tenant


def parse_tenant_arg(argv: list[str] | None = None) -> str:
    argv = argv if argv is not None else sys.argv[1:]
    for arg in argv:
        if arg.startswith("--tenant-id="):
            return arg.split("=", 1)[1].strip().lower()
    return DEFAULT_TENANT


def tenant_paths(tenant_id: str) -> dict[str, Path]:
    return effective_paths(resolve_tenant(tenant_id))


def queue_path(tenant_id: str) -> Path:
    return tenant_paths(tenant_id)["content_queue"]


def publish_log_path(tenant_id: str) -> Path:
    return resolve_tenant(tenant_id).publish_log_path


def meta_publish_log_path(tenant_id: str) -> Path:
    return resolve_tenant(tenant_id).meta_publish_log_path


def linkedin_credentials(tenant_id: str) -> tuple[str, str]:
    from Motor_Tecnico.accio_engine import tenant_secrets

    token = tenant_secrets.connector_env_value(tenant_id, "LINKEDIN_ACCESS_TOKEN")
    author = tenant_secrets.connector_env_value(tenant_id, "LINKEDIN_AUTHOR_URN")
    if not token or not author:
        raise SystemExit(
            f"Faltan credenciales LinkedIn para tenant '{tenant_id}'. "
            "Configúrelas en Configuración → Conectores y pulse Probar conexión."
        )
    return token, author


def meta_credentials(tenant_id: str) -> tuple[str, str, str | None]:
    from Motor_Tecnico.accio_engine import tenant_secrets

    page_id = tenant_secrets.connector_env_value(tenant_id, "META_PAGE_ID")
    token = tenant_secrets.connector_env_value(tenant_id, "META_PAGE_ACCESS_TOKEN")
    ig_id = tenant_secrets.connector_env_value(tenant_id, "META_IG_USER_ID") or None
    if not page_id or not token:
        raise SystemExit(
            f"Faltan credenciales Meta para tenant '{tenant_id}'. "
            "Configúrelas en Configuración → Conectores."
        )
    return page_id, token, ig_id


def resolve_flyer_path(post: dict, tenant_id: str) -> Path | None:
    from Motor_Tecnico.flyer_utils import resolve_flyer_path as _legacy_resolve

    flyer = (post.get("flyer") or "").strip()
    if not flyer:
        return None
    tenant = resolve_tenant(tenant_id)
    name = Path(flyer).name
    candidates = [
        tenant.root / flyer,
        tenant.root / "flyers" / name,
        tenant.flyers_dir / name,
        Path(__file__).resolve().parent.parent / "Marketing" / flyer,
        Path(__file__).resolve().parent.parent / "Marketing" / "flyers" / name,
    ]
    for path in candidates:
        if path.is_file():
            return path
    return _legacy_resolve(post)


def flyer_public_url(post: dict, public_base: str, tenant_id: str) -> str | None:
    path = resolve_flyer_path(post, tenant_id)
    if not path:
        return None
    return f"{public_base.rstrip('/')}/accio/assets/flyers/{path.name}"
