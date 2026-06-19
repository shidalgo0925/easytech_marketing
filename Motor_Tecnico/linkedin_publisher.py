#!/usr/bin/env python3
"""Publica el siguiente post pendiente de la cola en LinkedIn."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import requests
from dotenv import load_dotenv

from Motor_Tecnico.flyer_utils import resolve_flyer_path
QUEUE_PATH = BASE_DIR / "Marketing" / "content_queue.json"
LOG_PATH = BASE_DIR / "Marketing" / "publish_log.json"
PANAMA = ZoneInfo("America/Panama")

load_dotenv(BASE_DIR / ".env")

LINKEDIN_API = "https://api.linkedin.com/rest/posts"
LINKEDIN_VERSION = "202506"
IMAGE_WAIT_SEC = int(os.getenv("LINKEDIN_IMAGE_WAIT_SEC", "8"))


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


def _api_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": LINKEDIN_VERSION,
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }


def _image_content_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".webp":
        return "image/webp"
    return "image/png"


def wait_image_ready(token: str, image_urn: str, timeout_sec: int = 30) -> bool:
    encoded = urllib.parse.quote(image_urn, safe="")
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        resp = requests.get(
            f"https://api.linkedin.com/rest/images/{encoded}",
            headers=_api_headers(token),
            timeout=20,
        )
        if resp.ok:
            status = resp.json().get("status", "")
            if status == "AVAILABLE":
                return True
            if status == "PROCESSING_FAILED":
                print(f"  Imagen fallo procesamiento LinkedIn: {image_urn}")
                return False
        time.sleep(2)
    print(f"  Aviso: imagen no confirmada AVAILABLE tras {timeout_sec}s; se intenta publicar igual.")
    return True


def upload_image(token: str, author_urn: str, flyer_path: Path) -> str:
    init_resp = requests.post(
        "https://api.linkedin.com/rest/images?action=initializeUpload",
        headers=_api_headers(token),
        json={"initializeUploadRequest": {"owner": author_urn}},
        timeout=30,
    )
    if not init_resp.ok:
        raise RuntimeError(f"LinkedIn initializeUpload {init_resp.status_code}: {init_resp.text[:300]}")

    upload_info = init_resp.json()["value"]
    upload_url = upload_info["uploadUrl"]
    image_urn = upload_info["image"]

    content_type = _image_content_type(flyer_path)
    up_resp = requests.put(
        upload_url,
        data=flyer_path.read_bytes(),
        headers={"Content-Type": content_type},
        timeout=60,
    )
    if not up_resp.ok:
        raise RuntimeError(f"LinkedIn upload PUT {up_resp.status_code}: {up_resp.text[:300]}")

    if IMAGE_WAIT_SEC > 0:
        time.sleep(IMAGE_WAIT_SEC)
    wait_image_ready(token, image_urn)
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
                "id": image_urn,
                "altText": "EasyTech Services — marketing Panamá",
            }
        }

    resp = requests.post(LINKEDIN_API, headers=_api_headers(token), json=payload, timeout=30)
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
        headers=_api_headers(token),
        json={"actor": actor, "message": {"text": text}},
        timeout=30,
    )
    if not resp.ok:
        print(f"  Aviso: no se pudo publicar comentario ({resp.status_code}): {resp.text[:200]}")


def publish_next(force: bool = False, dry_run: bool = False, allow_text_only: bool = False) -> None:
    queue = load_queue()
    post = pick_next_post(queue, force=force)
    if not post:
        print("No hay posts pendientes listos para publicar.")
        return

    flyer_path = resolve_flyer_path(post)
    print(f"Post seleccionado: {post['id']} (programado: {post['scheduled_at']})")

    if dry_run:
        print("DRY RUN — no se publicó nada.")
        print(f"  Flyer: {flyer_path or 'NO ENCONTRADO'}")
        print(post["text"][:200] + "...")
        return

    if post.get("flyer") and not flyer_path and not allow_text_only:
        raise SystemExit(
            f"Flyer requerido pero no encontrado para {post['id']}: {post.get('flyer')}. "
            "Corrija la ruta o use --allow-text-only (no recomendado)."
        )

    token = require_env("LINKEDIN_ACCESS_TOKEN")
    author = require_env("LINKEDIN_AUTHOR_URN")

    image_urn = None
    if flyer_path:
        print(f"  Subiendo flyer: {flyer_path.name}")
        image_urn = upload_image(token, author, flyer_path)
        print(f"  Imagen URN: {image_urn}")
    elif not allow_text_only:
        raise SystemExit(f"Post {post['id']} sin flyer — abortado para evitar publicacion solo texto.")

    post_id = create_post(token, author, post["text"], image_urn)
    print(f"  Publicado: {post_id} (con imagen: {'si' if image_urn else 'no'})")

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
            item["published_with_image"] = bool(image_urn)
            if image_urn:
                item["linkedin_image_urn"] = image_urn
            break
    save_queue(queue)

    append_log(
        {
            "id": post["id"],
            "published_at": datetime.now(timezone.utc).isoformat(),
            "linkedin_post_id": post_id,
            "utm": post.get("utm"),
            "has_image": bool(image_urn),
            "flyer": post.get("flyer"),
            "flyer_file": flyer_path.name if flyer_path else None,
        }
    )
    print("Listo. Cola actualizada.")


def main() -> None:
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv
    allow_text_only = "--allow-text-only" in sys.argv
    publish_next(force=force, dry_run=dry_run, allow_text_only=allow_text_only)


if __name__ == "__main__":
    main()
