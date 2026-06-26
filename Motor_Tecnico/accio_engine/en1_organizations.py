#!/usr/bin/env python3
"""Fase 3 — sync read-only EN1 saas_organization ↔ EMAcción tenant_id.

Solo lectura hacia EN1: no crea ni modifica organizaciones en EN1.
EMAcción puede guardar `en1_organization_id` en registry.json para mapeo.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests

from Motor_Tecnico.accio_engine import tenant as tenant_mod

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SYNC_DIR = BASE_DIR / "Marketing" / "tenants" / ".en1"
CACHE_PATH = SYNC_DIR / "organizations_cache.json"
REFERENCE_PATH = SYNC_DIR / "reference_organizations.json"

DEFAULT_ORGS_PATH = os.getenv("EN1_ORGANIZATIONS_PATH", "/api/v1/saas/organizations").strip()
REQUEST_TIMEOUT = int(os.getenv("EN1_REQUEST_TIMEOUT", "20"))

# Referencia EN1 Dev (capturas /admin/organizations) — no sustituye API live.
REFERENCE_ORGANIZATIONS: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "Easy NodeOne - Dev",
        "subdomain": None,
        "status": "active",
        "registration": "open",
        "source": "reference",
    },
    {
        "id": 2,
        "name": "Taller Internacional",
        "subdomain": "tonydev",
        "status": "active",
        "registration": "open",
        "source": "reference",
    },
    {
        "id": 3,
        "name": "Relatic Panama Dev",
        "subdomain": None,
        "status": "active",
        "registration": "open",
        "source": "reference",
    },
    {
        "id": 4,
        "name": "Modecosa",
        "subdomain": "fisico",
        "status": "active",
        "registration": "open",
        "source": "reference",
    },
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_sync_dir() -> None:
    SYNC_DIR.mkdir(parents=True, exist_ok=True)
    if not REFERENCE_PATH.is_file():
        REFERENCE_PATH.write_text(
            json.dumps(
                {"updated_at": _utc_now(), "note": "Referencia EN1 Dev", "organizations": REFERENCE_ORGANIZATIONS},
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )


def resolve_credentials(tenant_id: str | None = None) -> tuple[str | None, str | None, str]:
    """URL, API key, orgs path — tenant CRM secrets primero, luego env global."""
    from Motor_Tecnico.accio_engine import tenant_secrets

    url = key = None
    if tenant_id:
        url = tenant_secrets.get_secret(tenant_id, "crm", "en1_api_url")
        key = tenant_secrets.get_secret(tenant_id, "crm", "en1_api_key")
    if not url:
        url = os.getenv("EN1_API_URL", "").strip() or None
    if not key:
        key = os.getenv("EN1_API_KEY", "").strip() or None
    path = os.getenv("EN1_ORGANIZATIONS_PATH", DEFAULT_ORGS_PATH).strip() or DEFAULT_ORGS_PATH
    return url, key, path


def _normalize_org(raw: dict[str, Any], *, source: str = "live") -> dict[str, Any]:
    org_id = raw.get("id") or raw.get("organization_id") or raw.get("saas_organization_id")
    name = (raw.get("name") or raw.get("display_name") or raw.get("nombre") or "").strip()
    subdomain = raw.get("subdomain") or raw.get("subdominio")
    status = (raw.get("status") or raw.get("estado") or "active").strip().lower()
    if status in ("activa", "active", "enabled"):
        status = "active"
    return {
        "id": org_id,
        "name": name,
        "subdomain": subdomain if subdomain not in ("-", "none", "") else None,
        "status": status,
        "registration": raw.get("registration") or raw.get("registro"),
        "source": source,
    }


def _parse_response(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        for key in ("organizations", "data", "results", "items", "records"):
            if isinstance(payload.get(key), list):
                rows = payload[key]
                break
        else:
            rows = [payload] if payload.get("id") or payload.get("organization_id") else []
    else:
        rows = []
    return [_normalize_org(r, source="live") for r in rows if isinstance(r, dict)]


def _auth_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "X-API-Key": api_key,
    }


def fetch_organizations(
    *,
    tenant_id: str | None = None,
    use_cache: bool = True,
    allow_reference: bool = True,
) -> dict[str, Any]:
    """GET read-only hacia EN1. Cachea éxito; fallback a cache o referencia."""
    _ensure_sync_dir()
    url, key, path = resolve_credentials(tenant_id)
    result: dict[str, Any] = {
        "ok": False,
        "source": None,
        "fetched_at": None,
        "organizations": [],
        "error": None,
        "api_configured": bool(url and key),
    }

    if url and key:
        endpoint = urljoin(url.rstrip("/") + "/", path.lstrip("/"))
        try:
            resp = requests.get(endpoint, headers=_auth_headers(key), timeout=REQUEST_TIMEOUT)
            if resp.ok:
                orgs = _parse_response(resp.json())
                result.update(
                    {
                        "ok": True,
                        "source": "live",
                        "fetched_at": _utc_now(),
                        "organizations": orgs,
                        "endpoint": endpoint,
                    }
                )
                CACHE_PATH.write_text(
                    json.dumps(
                        {
                            "fetched_at": result["fetched_at"],
                            "endpoint": endpoint,
                            "organizations": orgs,
                        },
                        indent=2,
                        ensure_ascii=False,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                return result
            result["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
        except requests.RequestException as exc:
            result["error"] = str(exc)
    else:
        result["error"] = "EN1 API no configurada (en1_api_url + en1_api_key o EN1_API_URL/EN1_API_KEY)"

    if use_cache and CACHE_PATH.is_file():
        try:
            cached = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            orgs = cached.get("organizations") or []
            if orgs:
                result.update(
                    {
                        "ok": True,
                        "source": "cache",
                        "fetched_at": cached.get("fetched_at"),
                        "organizations": orgs,
                        "endpoint": cached.get("endpoint"),
                        "error": result.get("error"),
                    }
                )
                return result
        except json.JSONDecodeError:
            pass

    if allow_reference:
        ref = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
        orgs = ref.get("organizations") or REFERENCE_ORGANIZATIONS
        result.update(
            {
                "ok": True,
                "source": "reference",
                "fetched_at": ref.get("updated_at"),
                "organizations": orgs,
                "error": result.get("error"),
                "note": "Datos de referencia EN1 Dev — configure API para sync live",
            }
        )
    return result


def _slugify(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return s[:48] or "org"


def _name_score(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def list_tenant_mappings() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in tenant_mod.load_registry().get("tenants", []):
        tid = raw.get("tenant_id")
        rows.append(
            {
                "tenant_id": tid,
                "display_name": raw.get("display_name", tid),
                "status": raw.get("status", "active"),
                "crm_target": raw.get("crm_target", "odoo"),
                "en1_organization_id": raw.get("en1_organization_id"),
                "en1_subdomain": raw.get("en1_subdomain"),
            }
        )
    return rows


def set_tenant_mapping(
    tenant_id: str,
    *,
    en1_organization_id: int | str | None,
    en1_subdomain: str | None = None,
) -> dict[str, Any]:
    """Actualiza solo registry EMAcción — no escribe en EN1."""
    tid = tenant_mod.normalize_tenant_id(tenant_id)
    reg = tenant_mod.load_registry()
    record = next((r for r in reg.get("tenants", []) if r.get("tenant_id") == tid), None)
    if not record:
        raise tenant_mod.TenantNotFoundError(f"Tenant no encontrado: {tid}")

    if en1_organization_id is None or en1_organization_id == "":
        record.pop("en1_organization_id", None)
        record.pop("en1_subdomain", None)
    else:
        record["en1_organization_id"] = int(en1_organization_id) if str(en1_organization_id).isdigit() else en1_organization_id
        if en1_subdomain is not None:
            record["en1_subdomain"] = en1_subdomain.strip() or None

    record["en1_mapped_at"] = _utc_now()
    tenant_mod.REGISTRY_PATH.write_text(
        json.dumps(reg, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return next(r for r in list_tenant_mappings() if r["tenant_id"] == tid)


def build_sync_report(*, tenant_id: str | None = None) -> dict[str, Any]:
    fetch = fetch_organizations(tenant_id=tenant_id)
    orgs = fetch.get("organizations") or []
    org_by_id = {str(o.get("id")): o for o in orgs if o.get("id") is not None}
    tenants = list_tenant_mappings()

    mapped: list[dict[str, Any]] = []
    unmapped_tenants: list[dict[str, Any]] = []
    suggestions: list[dict[str, Any]] = []

    for t in tenants:
        oid = t.get("en1_organization_id")
        if oid is not None:
            org = org_by_id.get(str(oid))
            mapped.append({**t, "en1_organization": org})
        else:
            unmapped_tenants.append(t)
            best = None
            best_score = 0.0
            for org in orgs:
                score = _name_score(t.get("display_name") or t["tenant_id"], org.get("name") or "")
                if score > best_score:
                    best_score = score
                    best = org
            if best and best_score >= 0.45:
                suggestions.append(
                    {
                        "tenant_id": t["tenant_id"],
                        "display_name": t.get("display_name"),
                        "suggested_en1_organization_id": best.get("id"),
                        "suggested_name": best.get("name"),
                        "score": round(best_score, 3),
                    }
                )

    mapped_org_ids = {str(t["en1_organization_id"]) for t in tenants if t.get("en1_organization_id") is not None}
    unmapped_orgs = [o for o in orgs if str(o.get("id")) not in mapped_org_ids]

    return {
        "ok": True,
        "fetch": {
            "source": fetch.get("source"),
            "fetched_at": fetch.get("fetched_at"),
            "count": len(orgs),
            "api_configured": fetch.get("api_configured"),
            "error": fetch.get("error"),
            "note": fetch.get("note"),
        },
        "mapped": mapped,
        "unmapped_tenants": unmapped_tenants,
        "unmapped_organizations": unmapped_orgs,
        "suggestions": suggestions,
    }


def test_en1_connection(tenant_id: str) -> dict[str, Any]:
    url, key, path = resolve_credentials(tenant_id)
    if not url:
        return {"ok": False, "error": "Falta en1_api_url"}
    if not key:
        return {"ok": False, "error": "Falta en1_api_key"}
    fetch = fetch_organizations(tenant_id=tenant_id, use_cache=False, allow_reference=False)
    if fetch.get("source") == "live":
        return {
            "ok": True,
            "detail": f"EN1 OK — {len(fetch.get('organizations') or [])} organizaciones",
            "endpoint": fetch.get("endpoint"),
        }
    return {"ok": False, "error": fetch.get("error") or "No se pudo leer organizaciones EN1"}
