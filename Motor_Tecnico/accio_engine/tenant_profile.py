#!/usr/bin/env python3
"""Perfil y branding por tenant (Fase B V2)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from Motor_Tecnico.accio_engine.tenant import REGISTRY_PATH, TENANTS_ROOT, resolve_tenant

_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
DEFAULT_BRANDING = {
    "primary_color": "#1a4a2e",
    "accent_color": "#2d6b44",
    "logo_url": "/accio/static/em-logomark.svg",
}


def _hex_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _profile_path(tenant_id: str) -> Path:
    return TENANTS_ROOT / tenant_id / "tenant.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_profile(tenant_id: str) -> dict[str, Any]:
    tenant = resolve_tenant(tenant_id)
    profile: dict[str, Any] = {
        "tenant_id": tenant.tenant_id,
        "display_name": tenant.display_name,
        "status": tenant.status,
        "crm_target": tenant.crm_target,
        "default_locale": tenant.default_locale,
        "domains": list(tenant.domains),
        "subdomain": tenant.subdomain,
        "registration": tenant.registration,
        "timezone": "America/Panama",
        "created_at": None,
        "branding": dict(DEFAULT_BRANDING),
    }
    path = _profile_path(tenant_id)
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        profile.update({k: v for k, v in data.items() if k != "branding"})
        branding = data.get("branding") or {}
        profile["branding"] = {**DEFAULT_BRANDING, **branding}
    return profile


def save_profile(tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    resolve_tenant(tenant_id)
    current = load_profile(tenant_id)
    allowed_top = {"display_name", "timezone", "domains", "default_locale", "subdomain", "registration"}
    for key in allowed_top:
        if key in payload:
            current[key] = payload[key]

    if "branding" in payload and isinstance(payload["branding"], dict):
        b = current.setdefault("branding", dict(DEFAULT_BRANDING))
        for bk, bv in payload["branding"].items():
            if bk in ("primary_color", "accent_color") and bv:
                if not _HEX_COLOR.match(str(bv)):
                    raise ValueError(f"Color inválido: {bv}")
                b[bk] = bv
            elif bk == "logo_url" and bv:
                url = str(bv).strip()
                tenant_assets = f"/accio/{tenant_id}/assets/"
                if not (
                    url.startswith(("/accio/static/", "https://"))
                    or url.startswith(tenant_assets)
                ):
                    raise ValueError("logo_url debe ser /accio/static/, /accio/{tenant}/assets/ o https://")
                b[bk] = url

    if not current.get("created_at"):
        current["created_at"] = _utc_now()
    current["updated_at"] = _utc_now()

    path = _profile_path(tenant_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    _sync_registry_display_name(tenant_id, current.get("display_name"))
    return current


def _sync_registry_display_name(tenant_id: str, display_name: str | None) -> None:
    if not display_name or not REGISTRY_PATH.is_file():
        return
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    for row in data.get("tenants", []):
        if row.get("tenant_id") == tenant_id:
            row["display_name"] = display_name
            break
    REGISTRY_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def branding_css(tenant_id: str) -> str:
    """Variables y controles UI alineados al tenant (dashboard + plan_slice)."""
    profile = load_profile(tenant_id)
    b = profile.get("branding") or DEFAULT_BRANDING
    primary = b.get("primary_color", DEFAULT_BRANDING["primary_color"])
    accent = b.get("accent_color", DEFAULT_BRANDING["accent_color"])
    r, g, bl = _hex_rgb(primary)
    tint_bg = f"rgba({r},{g},{bl},0.09)"
    tint_sel = f"rgba({r},{g},{bl},0.14)"
    tint_border = f"rgba({r},{g},{bl},0.22)"
    border_soft = f"rgba({r},{g},{bl},0.12)"
    return (
        f":root{{--tenant-brand-primary:{primary};--tenant-brand-accent:{accent};"
        f"--accent:{primary};--text-primary:{primary};"
        f"--green-700:{primary};--green-600:{primary};--green-400:{accent};--green-light:{primary};"
        f"--accent-bg:{tint_bg};--accent-border:{tint_border};--bg-selected:{tint_sel};"
        f"--border:{border_soft};--border-strong:rgba({r},{g},{bl},0.2);}}"
        f".btn-primary,.accio-btn-primary,.vs1-btn--primary{{background:{primary}!important;"
        f"border-color:{primary}!important;color:#fff!important}}"
        f".btn-primary:hover,.accio-btn-primary:hover,.vs1-btn--primary:hover{{"
        f"background:{accent}!important;border-color:{accent}!important}}"
        f".vs1-nav-item.is-active,.vs1-step-item.is-active .vs1-step-name{{color:{primary}}}"
        f".vs1-nav-item.is-active{{border-color:{primary}}}"
        f".vs1-logo-mark,.topbar-mark,.vs1-brand-wordmark,.brand-name,.brand-em,"
        f".topbar-brand .brand-name,.topbar-mark{{color:{primary}}}"
    )
