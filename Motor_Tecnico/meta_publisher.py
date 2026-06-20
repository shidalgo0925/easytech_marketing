#!/usr/bin/env python3
"""Publica posts pendientes en Facebook Page e Instagram Business (Meta Graph API)."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from Motor_Tecnico.flyer_utils import flyer_public_url, resolve_flyer_path
QUEUE_PATH = BASE_DIR / "Marketing" / "content_queue.json"
LOG_PATH = BASE_DIR / "Marketing" / "meta_publish_log.json"
PANAMA = ZoneInfo("America/Panama")
GRAPH = "https://graph.facebook.com/v21.0"
PUBLIC_BASE = os.getenv("PUBLIC_SITE_URL", "https://n8n.etsrv.site").rstrip("/")

load_dotenv(BASE_DIR / ".env")


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Falta variable de entorno: {name}")
    return value


def load_queue() -> dict:
    if not QUEUE_PATH.exists():
        raise SystemExit(f"No existe la cola: {QUEUE_PATH}")
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def save_queue(data: dict) -> None:
    QUEUE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_log(entry: dict) -> None:
    logs: list = []
    if LOG_PATH.exists():
        logs = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    logs.append(entry)
    LOG_PATH.write_text(json.dumps(logs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_scheduled(value: str) -> datetime:
    return datetime.fromisoformat(value)


def pick_next_post(queue: dict, platform: str, force: bool = False) -> dict | None:
    now = datetime.now(PANAMA)
    candidates = []
    for post in queue.get("posts", []):
        if post.get("platform") != platform:
            continue
        if post.get("status") != "pending":
            continue
        scheduled = parse_scheduled(post["scheduled_at"])
        if force or scheduled <= now:
            candidates.append((scheduled, post))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def publish_facebook(page_id: str, token: str, text: str, image_url: str | None) -> str:
    if image_url:
        resp = requests.post(
            f"{GRAPH}/{page_id}/photos",
            data={"url": image_url, "caption": text, "access_token": token},
            timeout=60,
        )
    else:
        resp = requests.post(
            f"{GRAPH}/{page_id}/feed",
            data={"message": text, "access_token": token},
            timeout=30,
        )
    if not resp.ok:
        raise RuntimeError(f"Facebook API {resp.status_code}: {resp.text}")
    data = resp.json()
    return str(data.get("post_id") or data.get("id") or "published")


def publish_instagram(ig_user_id: str, token: str, text: str, image_url: str | None) -> str:
    if not image_url:
        raise RuntimeError("Instagram requiere imagen (flyer).")
    create = requests.post(
        f"{GRAPH}/{ig_user_id}/media",
        data={"image_url": image_url, "caption": text, "access_token": token},
        timeout=60,
    )
    if not create.ok:
        raise RuntimeError(f"Instagram media {create.status_code}: {create.text}")
    creation_id = create.json()["id"]

    publish = requests.post(
        f"{GRAPH}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
        timeout=60,
    )
    if not publish.ok:
        raise RuntimeError(f"Instagram publish {publish.status_code}: {publish.text}")
    return str(publish.json().get("id") or creation_id)


def publish_platform(platform: str, force: bool = False, dry_run: bool = False) -> bool:
    queue = load_queue()
    post = pick_next_post(queue, platform, force=force)
    if not post:
        print(f"No hay posts {platform} pendientes listos para publicar.")
        return False

    print(f"Post seleccionado ({platform}): {post['id']} (programado: {post['scheduled_at']})")
    flyer_path = resolve_flyer_path(post)
    if dry_run:
        print("DRY RUN — no se publicó nada.")
        print(f"  Flyer: {flyer_path or 'NO ENCONTRADO'}")
        print(post["text"][:200] + "...")
        return True

    if post.get("flyer") and not flyer_path:
        raise SystemExit(f"Flyer requerido pero no encontrado: {post.get('flyer')}")

    page_id = require_env("META_PAGE_ID")
    token = require_env("META_PAGE_ACCESS_TOKEN")
    image_url = flyer_public_url(post, PUBLIC_BASE)

    if platform == "facebook":
        remote_id = publish_facebook(page_id, token, post["text"], image_url)
    elif platform == "instagram":
        ig_id = require_env("META_IG_USER_ID")
        remote_id = publish_instagram(ig_id, token, post["text"], image_url)
    else:
        raise SystemExit(f"Plataforma no soportada: {platform}")

    print(f"  Publicado: {remote_id}")

    for item in queue["posts"]:
        if item["id"] == post["id"]:
            item["status"] = "published"
            item["published_at"] = datetime.now(PANAMA).isoformat()
            item[f"{platform}_post_id"] = remote_id
            break
    save_queue(queue)

    append_log(
        {
            "id": post["id"],
            "platform": platform,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "remote_post_id": remote_id,
            "utm": post.get("utm"),
        }
    )
    print("Listo. Cola actualizada.")
    return True


def main() -> None:
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv
    platform = "facebook"
    for arg in sys.argv[1:]:
        if arg.startswith("--platform="):
            platform = arg.split("=", 1)[1].strip().lower()
        elif arg in ("facebook", "instagram"):
            platform = arg

    if platform == "all":
        ok_fb = publish_platform("facebook", force=force, dry_run=dry_run)
        ok_ig = publish_platform("instagram", force=force, dry_run=dry_run)
        if not ok_fb and not ok_ig:
            sys.exit(0)
        return

    publish_platform(platform, force=force, dry_run=dry_run)


if __name__ == "__main__":
    main()
