#!/usr/bin/env python3
"""Datos agregados para el dashboard Accio (multi-tenant)."""

from __future__ import annotations

import json
import os
import re
import xmlrpc.client
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from Motor_Tecnico.accio_engine import executor, metrics_store, queue_store
from Motor_Tecnico.accio_engine.editorial import editorial_label, is_publishable, normalize_status
from Motor_Tecnico.accio_engine.tenant import DEFAULT_TENANT, effective_paths, list_tenants, resolve_tenant
from Motor_Tecnico.connectors.registry import all_connector_views

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PANAMA = ZoneInfo("America/Panama")


def _paths(tenant_id: str, app_id: str | None = None) -> dict[str, Path]:
    from Motor_Tecnico.accio_engine import marketing_app

    base = effective_paths(resolve_tenant(tenant_id))
    if not app_id:
        return base
    aid = marketing_app.normalize_app_id(app_id)
    if aid == marketing_app.default_app_id(tenant_id):
        return base
    ap = marketing_app.effective_app_paths(tenant_id, aid)
    return {
        **base,
        "content_queue": ap["content_queue"],
        "calendar": ap["calendar"],
        "campaigns": ap["campaigns"],
    }


def load_connectors(tenant_id: str = DEFAULT_TENANT, app_id: str | None = None) -> list[dict[str, Any]]:
    return all_connector_views(tenant_id, app_id)


def _odoo_client(tenant_id: str = DEFAULT_TENANT):
    from Motor_Tecnico.accio_engine import tenant_secrets

    url = (
        tenant_secrets.get_secret(tenant_id, "crm", "odoo_url")
        or os.environ.get("ODOO_URL", "")
    ).rstrip("/")
    db = tenant_secrets.get_secret(tenant_id, "crm", "odoo_db") or os.environ.get("ODOO_DB", "")
    user = tenant_secrets.get_secret(tenant_id, "crm", "odoo_user") or os.environ.get("ODOO_USER", "")
    password = tenant_secrets.get_secret(tenant_id, "crm", "odoo_password") or os.environ.get("ODOO_PASSWORD", "")
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(db, user, password, {})
    if not uid:
        raise RuntimeError("Auth Odoo fallida")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    return db, uid, password, models, url


def fetch_odoo_leads(limit: int = 12, tenant_id: str = DEFAULT_TENANT) -> dict[str, Any]:
    STAGE_MARKETING = "Nuevo - Marketing"
    try:
        db, uid, password, models, url = _odoo_client(tenant_id)
        fields = ["name", "contact_name", "email_from", "phone", "create_date", "stage_id", "source_id"]
        leads = models.execute_kw(
            db,
            uid,
            password,
            "crm.lead",
            "search_read",
            [[]],
            {"fields": fields, "limit": limit, "order": "create_date desc"},
        )
        stage_ids = models.execute_kw(
            db,
            uid,
            password,
            "crm.stage",
            "search",
            [[("name", "=", STAGE_MARKETING)]],
            {"limit": 1},
        )
        marketing_count = 0
        if stage_ids:
            marketing_count = models.execute_kw(
                db,
                uid,
                password,
                "crm.lead",
                "search_count",
                [[("stage_id", "=", stage_ids[0])]],
            )
        total_count = models.execute_kw(db, uid, password, "crm.lead", "search_count", [[]])

        formatted = []
        for lead in leads:
            stage = lead.get("stage_id")
            source = lead.get("source_id")
            formatted.append(
                {
                    "id": lead["id"],
                    "name": lead.get("name") or "—",
                    "contact": lead.get("contact_name") or "—",
                    "email": lead.get("email_from") or "—",
                    "phone": lead.get("phone") or "—",
                    "created": lead.get("create_date") or "",
                    "stage": stage[1] if isinstance(stage, list) else "—",
                    "source": source[1] if isinstance(source, list) else "—",
                }
            )

        return {
            "ok": True,
            "total": total_count,
            "marketing_stage": marketing_count,
            "recent": formatted,
            "odoo_url": url,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "recent": [], "total": 0, "marketing_stage": 0}


def fetch_leads_by_source(tenant_id: str = DEFAULT_TENANT) -> dict[str, Any]:
    try:
        db, uid, password, models, _url = _odoo_client(tenant_id)
        groups = models.execute_kw(
            db,
            uid,
            password,
            "crm.lead",
            "read_group",
            [[]],
            {"fields": ["source_id"], "groupby": ["source_id"]},
        )
        by_source = []
        for group in groups:
            source = group.get("source_id")
            name = source[1] if isinstance(source, list) else "Sin origen"
            by_source.append({"source": name, "count": group.get("source_id_count", 0)})
        by_source.sort(key=lambda x: x["count"], reverse=True)
        return {"ok": True, "by_source": by_source}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "by_source": []}


def _flyer_num_from_post(post: dict[str, Any], manifest: dict[str, Any]) -> int | None:
    if post.get("flyer_num"):
        return int(post["flyer_num"])
    flyer = post.get("flyer") or ""
    match = re.search(r"(\d{2})_", flyer)
    if match:
        return int(match.group(1))
    for item in manifest.get("flyers", []):
        if item.get("file") and item["file"] in flyer:
            return item.get("num")
    return None


def _load_manifest(tenant_id: str) -> dict[str, Any]:
    from Motor_Tecnico.accio_engine.media_asset_infrastructure.facade import (
        asset_store_active,
        load_flyers_manifest,
    )

    if asset_store_active():
        return load_flyers_manifest(tenant_id)

    path = _paths(tenant_id)["flyers_manifest"]
    if not path.exists():
        return {"flyers": [], "extras": []}
    return json.loads(path.read_text(encoding="utf-8"))


def load_campaigns(tenant_id: str = DEFAULT_TENANT, app_id: str | None = None) -> list[dict[str, Any]]:
    from Motor_Tecnico.accio_engine.campaign_infrastructure.facade import (
        campaign_defs_by_post_id,
        campaign_store_active,
    )

    paths = _paths(tenant_id, app_id)
    manifest = _load_manifest(tenant_id)
    topic_by_num = {f["num"]: f.get("topic", "") for f in manifest.get("flyers", [])}
    defs: dict[str, dict[str, Any]] = {}
    if campaign_store_active():
        defs = campaign_defs_by_post_id(tenant_id, app_id)
    elif paths["campaigns"].exists():
        data = json.loads(paths["campaigns"].read_text(encoding="utf-8"))
        for camp in data.get("campaigns", []):
            if camp.get("post_id"):
                defs[camp["post_id"]] = camp

    queue = executor.load_content_queue_for_app(tenant_id, app_id)
    campaigns = []
    for post in queue.get("posts", []):
        post_id = post.get("id", "")
        flyer_num = _flyer_num_from_post(post, manifest)
        base = defs.get(post_id, {})
        campaigns.append(
            {
                "id": base.get("id") or post_id,
                "post_id": post_id,
                "product": base.get("product") or topic_by_num.get(flyer_num or 0, post_id),
                "flyer_num": flyer_num,
                "channel": post.get("platform", "linkedin"),
                "status": normalize_status(post.get("status")),
                "status_label": editorial_label(post.get("status")),
                "scheduled_at": post.get("scheduled_at"),
                "published_at": post.get("published_at"),
                "utm": post.get("utm"),
                "linkedin_post_id": post.get("linkedin_post_id"),
                "landing": base.get("landing", "https://n8n.etsrv.site/guia/"),
                "cta": base.get("cta", "DIAGNOSTICO"),
                "app_id": post.get("app_id"),
            }
        )
    campaigns.sort(key=lambda c: c.get("scheduled_at") or "")
    return campaigns


def load_calendar_view(tenant_id: str = DEFAULT_TENANT, app_id: str | None = None) -> dict[str, Any]:
    cal_path = _paths(tenant_id, app_id)["calendar"]
    if not cal_path.exists():
        return {"weeks": [], "timezone": "America/Panama"}
    calendar = json.loads(cal_path.read_text(encoding="utf-8"))
    queue_by_id = {
        p["id"]: p
        for p in executor.load_content_queue_for_app(tenant_id, app_id).get("posts", [])
        if p.get("id")
    }
    weeks = []
    for week in calendar.get("weeks", []):
        posts = []
        for item in week.get("posts", []):
            post_id = item.get("id")
            live = queue_by_id.get(post_id, {})
            posts.append(
                {
                    **item,
                    "status": normalize_status(live.get("status")),
                    "status_label": editorial_label(live.get("status")),
                    "published_at": live.get("published_at"),
                }
            )
        weeks.append({**week, "posts": posts})
    return {
        "updated_at": calendar.get("updated_at"),
        "timezone": calendar.get("timezone", "America/Panama"),
        "note": calendar.get("note"),
        "weeks": weeks,
    }


def load_flyers_library(tenant_id: str = DEFAULT_TENANT, app_id: str | None = None) -> dict[str, Any]:
    manifest = _load_manifest(tenant_id)
    queue = executor.load_content_queue_for_app(tenant_id, app_id)
    used_nums: set[int] = set()
    for post in queue.get("posts", []):
        num = _flyer_num_from_post(post, manifest)
        if num:
            used_nums.add(num)

    items = []
    for flyer in manifest.get("flyers", []):
        num = flyer.get("num")
        file_name = flyer.get("file")
        missing = flyer.get("status") == "missing" or not file_name
        items.append(
            {
                "num": num,
                "topic": flyer.get("topic"),
                "file": file_name,
                "missing": missing,
                "in_queue": num in used_nums if num else False,
                "url": f"/accio/assets/flyers/{file_name}" if file_name else None,
            }
        )

    extras = []
    for extra in manifest.get("extras", []):
        file_name = extra.get("file")
        extras.append(
            {
                "topic": extra.get("topic"),
                "file": file_name,
                "url": f"/accio/assets/flyers/{file_name}" if file_name else None,
            }
        )

    return {
        "updated": manifest.get("updated"),
        "contact": manifest.get("contact", {}),
        "flyers": items,
        "extras": extras,
        "total": len(items),
        "available": sum(1 for f in items if not f["missing"]),
        "missing": sum(1 for f in items if f["missing"]),
    }


def load_metrics(tenant_id: str = DEFAULT_TENANT, app_id: str | None = None) -> dict[str, Any]:
    paths = _paths(tenant_id, app_id)
    status = executor.get_status(tenant_id, app_id)
    publish_log: list[dict[str, Any]] = []
    pl_path = paths["publish_log"]
    if pl_path.exists():
        publish_log = json.loads(pl_path.read_text(encoding="utf-8"))

    sources = fetch_leads_by_source(tenant_id)
    guia_leads = 0
    scraper_leads = 0
    linkedin_leads = 0
    if sources.get("ok"):
        for row in sources["by_source"]:
            name = row["source"].lower()
            if "guia" in name:
                guia_leads += row["count"]
            elif "scraper" in name:
                scraper_leads += row["count"]
            elif "linkedin" in name:
                linkedin_leads += row["count"]

    published = status["content_queue"]["linkedin_published"]
    pending = status["content_queue"]["linkedin_pending"]
    odoo = fetch_odoo_leads(limit=1, tenant_id=tenant_id)
    total_leads = odoo.get("total", 0) if odoo.get("ok") else 0
    marketing_leads = odoo.get("marketing_stage", 0) if odoo.get("ok") else 0

    conversion_rate = round((guia_leads / published) * 100, 1) if published else 0.0

    return {
        "linkedin": {
            "published": published,
            "pending": pending,
            "publish_log_entries": len(publish_log),
            "recent_published": publish_log[-3:][::-1] if publish_log else [],
        },
        "app_events": metrics_store.summary_for_dashboard(tenant_id, app_id),
        "prospection": {"csv_rows": status["prospection_csv_rows"]},
        "odoo": {
            "total_leads": total_leads,
            "marketing_stage": marketing_leads,
            "by_source": sources.get("by_source", []),
            "guia_leads": guia_leads,
            "scraper_leads": scraper_leads,
            "linkedin_leads": linkedin_leads,
        },
        "conversion": {
            "guia_per_post": conversion_rate,
            "note": "Clicks en guia requieren analytics web; conversion = leads guia_fe / posts publicados",
        },
        "orders_pending": status["orders_pending"],
    }


def pending_posts(tenant_id: str = DEFAULT_TENANT, app_id: str | None = None) -> list[dict[str, Any]]:
    queue = executor.load_content_queue_for_app(tenant_id, app_id)
    items = []
    for post in queue.get("posts", []):
        if not is_publishable(post.get("status")):
            continue
        flyer = post.get("flyer", "")
        st = normalize_status(post.get("status"))
        items.append(
            {
                "id": post.get("id"),
                "platform": post.get("platform"),
                "scheduled_at": post.get("scheduled_at"),
                "flyer": flyer.split("/")[-1] if flyer else "—",
                "preview": (post.get("text") or "")[:120] + "…",
                "utm": post.get("utm"),
                "status": st,
                "status_label": editorial_label(st),
                "app_id": post.get("app_id"),
            }
        )
    items.sort(key=lambda p: p.get("scheduled_at") or "")
    return items


def published_posts(
    limit: int = 5, tenant_id: str = DEFAULT_TENANT, app_id: str | None = None
) -> list[dict[str, Any]]:
    queue = executor.load_content_queue_for_app(tenant_id, app_id)
    items = [p for p in queue.get("posts", []) if p.get("status") == "published"]
    items.sort(key=lambda p: p.get("published_at") or "", reverse=True)
    return [
        {
            "id": p.get("id"),
            "published_at": p.get("published_at"),
            "linkedin_post_id": p.get("linkedin_post_id"),
        }
        for p in items[:limit]
    ]


def get_summary(tenant_id: str = DEFAULT_TENANT, app_id: str | None = None) -> dict[str, Any]:
    from Motor_Tecnico.accio_engine import marketing_app

    tenant = resolve_tenant(tenant_id)
    aid = marketing_app.normalize_app_id(app_id or marketing_app.default_app_id(tenant_id))
    status = executor.get_status(tenant_id, aid)
    orders = queue_store.list_orders(limit=15, tenant_id=tenant_id)
    tenants_meta = [
        {"tenant_id": t.tenant_id, "display_name": t.display_name}
        for t in list_tenants()
    ]
    apps_meta = [a.to_dict() for a in marketing_app.list_apps(tenant_id)]
    app_row = next((a for a in apps_meta if a["app_id"] == aid), None)
    return {
        "ok": True,
        "tenant_id": tenant_id,
        "tenant_name": tenant.display_name,
        "app_id": aid,
        "app_name": (app_row or {}).get("name", aid),
        "default_app_id": marketing_app.default_app_id(tenant_id),
        "apps": apps_meta,
        "tenants": tenants_meta,
        "time_panama": datetime.now(PANAMA).strftime("%Y-%m-%d %H:%M %Z"),
        "stats": {
            "linkedin_pending": status["content_queue"]["linkedin_pending"],
            "linkedin_published": status["content_queue"]["linkedin_published"],
            "facebook_pending": status["content_queue"].get("facebook_pending", 0),
            "instagram_pending": status["content_queue"].get("instagram_pending", 0),
            "prospection_csv": status["prospection_csv_rows"],
            "orders_pending": status["orders_pending"],
            "editorial": status.get("editorial", {}),
        },
        "pending_posts": pending_posts(tenant_id, aid),
        "published_posts": published_posts(tenant_id=tenant_id, app_id=aid),
        "campaigns": load_campaigns(tenant_id, aid),
        "calendar": load_calendar_view(tenant_id, aid),
        "metrics": load_metrics(tenant_id, aid),
        "flyers": load_flyers_library(tenant_id, aid),
        "connectors": load_connectors(tenant_id, aid),
        "orders": orders,
        "odoo": fetch_odoo_leads(tenant_id=tenant_id),
        "links": {
            "n8n": "https://n8n.etsrv.site",
            "guia": "https://n8n.etsrv.site/guia/",
            "linkedin_oauth": "https://n8n.etsrv.site/linkedin/",
            "meta_oauth": "https://n8n.etsrv.site/meta/",
        },
    }
