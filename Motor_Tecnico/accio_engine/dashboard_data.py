#!/usr/bin/env python3
"""Datos agregados para el dashboard Accio."""

from __future__ import annotations

import json
import os
import re
import xmlrpc.client
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from Motor_Tecnico.accio_engine import executor, queue_store
from Motor_Tecnico.connectors.registry import all_connector_views

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PANAMA = ZoneInfo("America/Panama")
STAGE_MARKETING = "Nuevo - Marketing"
CAMPAIGNS_PATH = BASE_DIR / "Marketing" / "accio" / "campaigns.json"
CALENDAR_PATH = BASE_DIR / "Marketing" / "accio" / "calendar.json"
MANIFEST_PATH = BASE_DIR / "Marketing" / "flyers" / "manifest.json"
PUBLISH_LOG_PATH = BASE_DIR / "Marketing" / "publish_log.json"
META_LOG_PATH = BASE_DIR / "Marketing" / "meta_publish_log.json"
FLYERS_DIR = BASE_DIR / "Marketing" / "flyers"


def load_connectors() -> list[dict[str, Any]]:
    return all_connector_views()


def _odoo_client():
    url = os.environ["ODOO_URL"].rstrip("/")
    db = os.environ["ODOO_DB"]
    user = os.environ["ODOO_USER"]
    password = os.environ["ODOO_PASSWORD"]
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(db, user, password, {})
    if not uid:
        raise RuntimeError("Auth Odoo fallida")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    return db, uid, password, models


def fetch_odoo_leads(limit: int = 12) -> dict[str, Any]:
    try:
        db, uid, password, models = _odoo_client()
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
            "odoo_url": os.environ.get("ODOO_URL", "").rstrip("/"),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "recent": [], "total": 0, "marketing_stage": 0}


def fetch_leads_by_source() -> dict[str, Any]:
    try:
        db, uid, password, models = _odoo_client()
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


def _load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        return {"flyers": [], "extras": []}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_campaigns() -> list[dict[str, Any]]:
    manifest = _load_manifest()
    topic_by_num = {f["num"]: f.get("topic", "") for f in manifest.get("flyers", [])}
    defs: dict[str, dict[str, Any]] = {}
    if CAMPAIGNS_PATH.exists():
        data = json.loads(CAMPAIGNS_PATH.read_text(encoding="utf-8"))
        for camp in data.get("campaigns", []):
            if camp.get("post_id"):
                defs[camp["post_id"]] = camp

    queue = executor.load_content_queue()
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
                "status": post.get("status", "pending"),
                "scheduled_at": post.get("scheduled_at"),
                "published_at": post.get("published_at"),
                "utm": post.get("utm"),
                "linkedin_post_id": post.get("linkedin_post_id"),
                "landing": base.get("landing", "https://n8n.etsrv.site/guia/"),
                "cta": base.get("cta", "DIAGNOSTICO"),
            }
        )
    campaigns.sort(key=lambda c: c.get("scheduled_at") or "")
    return campaigns


def load_calendar_view() -> dict[str, Any]:
    if not CALENDAR_PATH.exists():
        return {"weeks": [], "timezone": "America/Panama"}
    calendar = json.loads(CALENDAR_PATH.read_text(encoding="utf-8"))
    queue_by_id = {p["id"]: p for p in executor.load_content_queue().get("posts", []) if p.get("id")}
    weeks = []
    for week in calendar.get("weeks", []):
        posts = []
        for item in week.get("posts", []):
            post_id = item.get("id")
            live = queue_by_id.get(post_id, {})
            posts.append(
                {
                    **item,
                    "status": live.get("status", "pending"),
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


def load_flyers_library() -> dict[str, Any]:
    manifest = _load_manifest()
    queue = executor.load_content_queue()
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


def load_metrics() -> dict[str, Any]:
    status = executor.get_status()
    publish_log: list[dict[str, Any]] = []
    if PUBLISH_LOG_PATH.exists():
        publish_log = json.loads(PUBLISH_LOG_PATH.read_text(encoding="utf-8"))

    sources = fetch_leads_by_source()
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
    odoo = fetch_odoo_leads(limit=1)
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


def pending_posts() -> list[dict[str, Any]]:
    queue = executor.load_content_queue()
    items = []
    for post in queue.get("posts", []):
        if post.get("status") != "pending":
            continue
        flyer = post.get("flyer", "")
        items.append(
            {
                "id": post.get("id"),
                "platform": post.get("platform"),
                "scheduled_at": post.get("scheduled_at"),
                "flyer": flyer.split("/")[-1] if flyer else "—",
                "preview": (post.get("text") or "")[:120] + "…",
                "utm": post.get("utm"),
            }
        )
    items.sort(key=lambda p: p.get("scheduled_at") or "")
    return items


def published_posts(limit: int = 5) -> list[dict[str, Any]]:
    queue = executor.load_content_queue()
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


def get_summary() -> dict[str, Any]:
    status = executor.get_status()
    orders = queue_store.list_orders(limit=15)
    return {
        "ok": True,
        "time_panama": datetime.now(PANAMA).strftime("%Y-%m-%d %H:%M %Z"),
        "stats": {
            "linkedin_pending": status["content_queue"]["linkedin_pending"],
            "linkedin_published": status["content_queue"]["linkedin_published"],
            "facebook_pending": status["content_queue"].get("facebook_pending", 0),
            "instagram_pending": status["content_queue"].get("instagram_pending", 0),
            "prospection_csv": status["prospection_csv_rows"],
            "orders_pending": status["orders_pending"],
        },
        "pending_posts": pending_posts(),
        "published_posts": published_posts(),
        "campaigns": load_campaigns(),
        "calendar": load_calendar_view(),
        "metrics": load_metrics(),
        "flyers": load_flyers_library(),
        "connectors": load_connectors(),
        "orders": orders,
        "odoo": fetch_odoo_leads(),
        "links": {
            "n8n": "https://n8n.etsrv.site",
            "guia": "https://n8n.etsrv.site/guia/",
            "linkedin_oauth": "https://n8n.etsrv.site/linkedin/",
            "meta_oauth": "https://n8n.etsrv.site/meta/",
        },
    }
