#!/usr/bin/env python3
"""Servicio unificado de configuración por tenant."""

from __future__ import annotations

from typing import Any

from Motor_Tecnico.accio_engine import settings_center, tenant_secrets


def get_connectors_view(tenant_id: str) -> dict[str, Any]:
    return tenant_secrets.get_settings_view(tenant_id).get("connectors", {})


def get_center_view(tenant_id: str) -> dict[str, Any]:
    return settings_center.get_center_view(tenant_id)


def save_connectors(tenant_id: str, payload: dict[str, Any], *, actor: str = "dashboard") -> dict[str, Any]:
    return tenant_secrets.save_settings_section(tenant_id, "connectors", payload, actor=actor)


def save_crm(tenant_id: str, payload: dict[str, Any], *, actor: str = "dashboard") -> dict[str, Any]:
    return tenant_secrets.save_settings_section(tenant_id, "crm", payload, actor=actor)


def save_platform(tenant_id: str, payload: dict[str, Any], *, actor: str = "dashboard") -> dict[str, Any]:
    return tenant_secrets.save_settings_section(tenant_id, "platform", payload, actor=actor)


def test_connector(tenant_id: str, connector_id: str) -> dict[str, Any]:
    return tenant_secrets.test_connector(tenant_id, connector_id)


def test_crm(tenant_id: str) -> dict[str, Any]:
    return tenant_secrets.test_crm(tenant_id)


def get_credentials_for_channel(tenant_id: str, channel: str) -> dict[str, str]:
    """Credenciales runtime para publishers — nunca para UI."""
    channel = channel.lower()
    if channel == "linkedin":
        from Motor_Tecnico.publisher_tenant import linkedin_credentials

        token, author = linkedin_credentials(tenant_id)
        return {"linkedin_access_token": token, "linkedin_author_urn": author}
    if channel in ("facebook", "instagram", "meta"):
        from Motor_Tecnico.publisher_tenant import meta_credentials

        page_id, token, ig_id = meta_credentials(tenant_id)
        out = {"meta_page_id": page_id, "meta_page_access_token": token}
        if ig_id:
            out["meta_ig_user_id"] = ig_id
        return out
    raise ValueError(f"Canal no soportado: {channel}")
