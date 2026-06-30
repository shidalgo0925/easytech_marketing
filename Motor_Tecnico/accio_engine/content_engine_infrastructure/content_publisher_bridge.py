"""Bridge Content Engine → legacy content_queue + linkedin_publisher (VS2)."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from Motor_Tecnico.accio_engine.content_engine_domain.model import ContentPiece
from Motor_Tecnico.accio_engine.content_engine_infrastructure.publish_config import PublishConfig

PANAMA = ZoneInfo("America/Panama")


def format_post_text(piece: ContentPiece) -> str:
    parts: list[str] = []
    if piece.headline:
        parts.append(piece.headline.strip())
    if piece.body:
        parts.append(piece.body.strip())
    if piece.call_to_action:
        parts.append(f"👉 {piece.call_to_action.strip()}")
    if piece.hashtags:
        parts.append(" ".join(piece.hashtags))
    return "\n\n".join(p for p in parts if p)


def linkedin_post_url(post_id: str | None) -> str | None:
    if not post_id or post_id.startswith("dry_"):
        return None
    if post_id.startswith("urn:"):
        return f"https://www.linkedin.com/feed/update/{post_id}"
    return f"https://www.linkedin.com/feed/update/urn:li:share:{post_id}"


def piece_to_queue_post(piece: ContentPiece) -> dict[str, Any]:
    post_id = piece.queue_post_id or piece.content_id
    now = datetime.now(PANAMA).isoformat()
    return {
        "id": post_id,
        "platform": piece.channel or "linkedin",
        "status": "approved",
        "scheduled_at": now,
        "text": format_post_text(piece),
        "flyer": piece.flyer_ref or "",
        "content_type": piece.content_type,
        "app_id": piece.brand_id,
        "source": "content_engine",
        "content_id": piece.content_id,
        "campaign_id": piece.campaign_id,
    }


class ContentPublisherBridge:
    def __init__(self, config: PublishConfig | None = None) -> None:
        self._config = config or PublishConfig.from_env()

    @property
    def config(self) -> PublishConfig:
        return self._config

    def has_linkedin_credentials(self, tenant_id: str) -> bool:
        from Motor_Tecnico.accio_engine import tenant_secrets

        token = tenant_secrets.connector_env_value(tenant_id, "LINKEDIN_ACCESS_TOKEN")
        author = tenant_secrets.connector_env_value(tenant_id, "LINKEDIN_AUTHOR_URN")
        return bool(token and author)

    def enqueue_piece(self, piece: ContentPiece, tenant_id: str) -> dict[str, Any]:
        from Motor_Tecnico.accio_engine import executor

        post = piece_to_queue_post(piece)
        app_id = piece.brand_id
        try:
            return executor.enqueue_post(post, tenant_id, app_id)
        except ValueError as exc:
            if "duplicado" in str(exc).lower():
                return post
            raise

    def find_queue_post(
        self, tenant_id: str, post_id: str, app_id: str | None
    ) -> dict[str, Any] | None:
        from Motor_Tecnico.accio_engine import executor

        queue = executor.load_content_queue(tenant_id, app_id)
        for post in queue.get("posts", []):
            if post.get("id") == post_id:
                return post
        return None

    def publish_piece(
        self,
        piece: ContentPiece,
        tenant_id: str,
        *,
        dry_run: bool | None = None,
        force: bool = True,
    ) -> dict[str, Any]:
        from Motor_Tecnico.accio_engine import executor

        channel = (piece.channel or "linkedin").lower()
        block = self._config.explain_block(channel)
        if block:
            return {
                "ok": False,
                "status": "failed",
                "skipped": True,
                "dry_run": False,
                "error_message": block,
            }

        if channel != "linkedin":
            return {
                "ok": False,
                "status": "failed",
                "dry_run": False,
                "error_message": f"Canal no soportado en VS2: {channel}",
            }

        use_dry_run = self._config.dry_run if dry_run is None else dry_run
        post_id = piece.queue_post_id or piece.content_id

        if use_dry_run:
            now = datetime.now(PANAMA).isoformat()
            external_id = f"dry_{piece.content_id}"
            return {
                "ok": True,
                "status": "published",
                "dry_run": True,
                "content_id": piece.content_id,
                "channel": channel,
                "published_at": now,
                "external_post_id": external_id,
                "external_url": None,
                "queue_post_id": post_id,
                "simulated": True,
            }

        if not self.has_linkedin_credentials(tenant_id):
            return {
                "ok": False,
                "status": "failed",
                "dry_run": False,
                "skipped": True,
                "error_message": (
                    "Sin credenciales LinkedIn. Configure LINKEDIN_ACCESS_TOKEN y "
                    "LINKEDIN_AUTHOR_URN en Conectores."
                ),
            }

        self.enqueue_piece(replace(piece, queue_post_id=post_id), tenant_id)
        pub = executor.publish_linkedin(
            force=force,
            dry_run=False,
            tenant_id=tenant_id,
            app_id=piece.brand_id,
        )

        queued = self.find_queue_post(tenant_id, post_id, piece.brand_id)
        if queued and queued.get("status") == "published":
            ext_id = queued.get("linkedin_post_id")
            return {
                "ok": True,
                "status": "published",
                "dry_run": False,
                "content_id": piece.content_id,
                "channel": channel,
                "published_at": queued.get("published_at"),
                "external_post_id": ext_id,
                "external_url": linkedin_post_url(ext_id),
                "queue_post_id": post_id,
                "publisher_stdout": (pub.get("stdout") or "")[-2000:],
            }

        err = (pub.get("stderr") or pub.get("stdout") or "No se pudo publicar en LinkedIn").strip()
        return {
            "ok": False,
            "status": "failed",
            "dry_run": False,
            "error_message": err[:500],
            "queue_post_id": post_id,
            "publisher_result": pub,
        }
