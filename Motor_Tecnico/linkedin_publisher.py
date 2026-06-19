#!/usr/bin/env python3
"""Publica el siguiente post pendiente de la cola en LinkedIn."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
QUEUE_PATH = BASE_DIR / "Marketing" / "content_queue.json"
LOG_PATH = BASE_DIR / "Marketing" / "publish_log.json"
PANAMA = ZoneInfo("America/Panama")

load_dotenv(BASE_DIR / ".env")

LINKEDIN_API = "https://api.linkedin.com/rest/posts"
LINKEDIN_VERSION = "202506"


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


def pick_next_post(queue: dict, force: bool = False) -> dict | None:
    now = datetime.now(PANAMA)
    candidates = []
    for post in queue.get("posts", []):
        if post.get("platform") != "linkedin":
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


def upload_image_if_exists(token: str, author_urn: str, flyer_path: Path) -> str | None:
    if not flyer_path.exists():
        print(f"  Flyer no encontrado ({flyer_path}); se publica solo texto.")
        return None

    init_resp = requests.post(
        "https://api.linkedin.com/rest/images?action=initializeUpload",
        headers={
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": LINKEDIN_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        },
        json={"initializeUploadRequest": {"owner": author_urn}},
        timeout=30,
    )
    init_resp.raise_for_status()
    upload_info = init_resp.json()["value"]
    upload_url = upload_info["uploadUrl"]
    image_urn = upload_info["image"]

    image_bytes = flyer_path.read_bytes()
    up_resp = requests.put(
        upload_url,
        data=image_bytes,
        headers={"Content-Type": "application/octet-stream"},
        timeout=60,
    )
    up_resp.raise_for_status()
    return image_urn


def create_post(token: str, author_urn: str, text: str, image_urn: str | None) -> str:
    payload: dict = {
        "author": author_urn,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED"},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    if image_urn:
        payload["content"] = {
            "media": {
                "title": "EasyTech Services",
                "id": image_urn,
            }
        }

    resp = requests.post(
        LINKEDIN_API,
        headers={
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": LINKEDIN_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"LinkedIn API {resp.status_code}: {resp.text}")

    post_id = resp.headers.get("x-restli-id") or resp.headers.get("X-RestLi-Id")
    if not post_id and resp.text:
        try:
            post_id = resp.json().get("id")
        except Exception:
            post_id = None
    return post_id or "published"


def create_comment(token: str, post_urn: str, text: str) -> None:
    if not post_urn.startswith("urn:"):
        post_urn = f"urn:li:share:{post_urn}"
    actor = require_env("LINKEDIN_AUTHOR_URN")
    resp = requests.post(
        "https://api.linkedin.com/rest/socialActions/{}/comments".format(post_urn.split(":")[-1]),
        headers={
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": LINKEDIN_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        },
        json={"actor": actor, "message": {"text": text}},
        timeout=30,
    )
    if not resp.ok:
        print(f"  Aviso: no se pudo publicar comentario ({resp.status_code}): {resp.text[:200]}")


def publish_next(force: bool = False, dry_run: bool = False) -> None:
    queue = load_queue()
    post = pick_next_post(queue, force=force)
    if not post:
        print("No hay posts pendientes listos para publicar.")
        return

    print(f"Post seleccionado: {post['id']} (programado: {post['scheduled_at']})")
    if dry_run:
        print("DRY RUN — no se publicó nada.")
        print(post["text"][:200] + "...")
        return

    token = require_env("LINKEDIN_ACCESS_TOKEN")
    author = require_env("LINKEDIN_AUTHOR_URN")
    flyer = BASE_DIR / "Marketing" / post.get("flyer", "")

    image_urn = upload_image_if_exists(token, author, flyer)
    post_id = create_post(token, author, post["text"], image_urn)
    print(f"  Publicado: {post_id}")

    first_comment = post.get("first_comment", "").strip()
    if first_comment:
        print("  Esperando 2 min para primer comentario...")
        time.sleep(120)
        create_comment(token, post_id, first_comment)

    for item in queue["posts"]:
        if item["id"] == post["id"]:
            item["status"] = "published"
            item["published_at"] = datetime.now(PANAMA).isoformat()
            item["linkedin_post_id"] = post_id
            break
    save_queue(queue)

    append_log(
        {
            "id": post["id"],
            "published_at": datetime.now(timezone.utc).isoformat(),
            "linkedin_post_id": post_id,
            "utm": post.get("utm"),
        }
    )
    print("Listo. Cola actualizada.")


def main() -> None:
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv
    publish_next(force=force, dry_run=dry_run)


if __name__ == "__main__":
    main()
