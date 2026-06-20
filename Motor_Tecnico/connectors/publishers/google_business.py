#!/usr/bin/env python3
"""Publicador Google Business Profile — local posts v4."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from Motor_Tecnico.connectors.google_auth import google_access_token  # noqa: E402
from Motor_Tecnico.connectors.queue_tools import append_log, load_queue, pick_next_post, save_queue  # noqa: E402
from Motor_Tecnico.flyer_utils import flyer_public_url, resolve_flyer_path  # noqa: E402

PANAMA = ZoneInfo("America/Panama")
PUBLIC_BASE = os.getenv("PUBLIC_SITE_URL", "https://n8n.etsrv.site").rstrip("/")
LOG_FILE = "Marketing/publish_logs/google_business.json"

load_dotenv(BASE_DIR / ".env")


def location_resource_name() -> str:
    loc = os.getenv("GOOGLE_BUSINESS_LOCATION_ID", "").strip()
    if not loc:
        raise RuntimeError("Falta GOOGLE_BUSINESS_LOCATION_ID — conectar en /google/")
    if loc.startswith("accounts/"):
        return loc
    account = os.getenv("GOOGLE_BUSINESS_ACCOUNT_ID", "").strip()
    if account and not account.startswith("accounts/"):
        account = f"accounts/{account}"
    if account and loc.isdigit():
        return f"{account}/locations/{loc}"
    return loc


def publish_local_post(text: str, image_url: str | None) -> str:
    token = google_access_token()
    parent = location_resource_name()
    url = f"https://mybusiness.googleapis.com/v4/{parent}/localPosts"
    body: dict = {
        "languageCode": "es",
        "summary": text[:1500],
        "topicType": "STANDARD",
    }
    if image_url:
        body["media"] = [{"mediaFormat": "PHOTO", "sourceUrl": image_url}]

    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body,
        timeout=60,
    )
    if not resp.ok:
        raise RuntimeError(f"Google Business API {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    return str(data.get("name") or data.get("searchUrl") or "published")


def main() -> None:
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv
    queue = load_queue()
    post = pick_next_post(queue, "google_business", force=force)
    if not post:
        print("No hay posts google_business pendientes listos para publicar.")
        return

    print(f"Post seleccionado (google_business): {post['id']} ({post['scheduled_at']})")
    flyer_path = resolve_flyer_path(post)
    image_url = flyer_public_url(post, PUBLIC_BASE)

    if dry_run:
        print("DRY RUN — no se publico nada.")
        print(f"  Flyer: {flyer_path or 'NO'}")
        print((post.get("text") or "")[:200])
        return

    if post.get("flyer") and not flyer_path:
        raise SystemExit(f"Flyer requerido pero no encontrado: {post.get('flyer')}")

    remote_id = publish_local_post(post["text"], image_url)
    print(f"  Publicado: {remote_id}")

    for item in queue["posts"]:
        if item["id"] == post["id"]:
            item["status"] = "published"
            item["published_at"] = datetime.now(PANAMA).isoformat()
            item["google_business_post_id"] = remote_id
            break
    save_queue(queue)
    append_log(
        LOG_FILE,
        {
            "id": post["id"],
            "platform": "google_business",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "remote_post_id": remote_id,
            "utm": post.get("utm"),
        },
    )
    print("Listo.")


if __name__ == "__main__":
    main()
