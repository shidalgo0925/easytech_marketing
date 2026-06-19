#!/usr/bin/env python3
"""Datos agregados para el dashboard Accio."""

from __future__ import annotations

import os
import xmlrpc.client
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from Motor_Tecnico.accio_engine import executor, queue_store

PANAMA = ZoneInfo("America/Panama")
STAGE_MARKETING = "Nuevo - Marketing"


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
            "prospection_csv": status["prospection_csv_rows"],
            "orders_pending": status["orders_pending"],
        },
        "pending_posts": pending_posts(),
        "published_posts": published_posts(),
        "orders": orders,
        "odoo": fetch_odoo_leads(),
        "links": {
            "n8n": "https://n8n.etsrv.site",
            "guia": "https://n8n.etsrv.site/guia/",
            "linkedin_oauth": "https://n8n.etsrv.site/linkedin/",
        },
    }
