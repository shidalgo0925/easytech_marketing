"""Defaults del dominio — implementaciones triviales de puertos (sin infraestructura)."""

from __future__ import annotations


class AcceptAllTenantAppValidator:
    def tenant_exists(self, tenant_id: str) -> bool:
        return bool(tenant_id.strip())

    def app_exists(self, tenant_id: str, app_id: str) -> bool:
        return bool(tenant_id.strip() and app_id.strip())
