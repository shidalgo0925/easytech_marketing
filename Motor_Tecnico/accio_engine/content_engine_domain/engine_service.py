from __future__ import annotations

import secrets
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.content_engine_domain.constants import CONTENT_STATUSES, PUBLISH_QUEUE_STATUSES
from Motor_Tecnico.accio_engine.content_engine_domain.errors import ContentEngineError, ContentInvalidStatus, ContentNotFound
from Motor_Tecnico.accio_engine.content_engine_domain.model import ContentPiece
from Motor_Tecnico.accio_engine.content_engine_domain.ports import ContentEngineRepository
from Motor_Tecnico.accio_engine.content_engine_infrastructure.content_publisher_bridge import ContentPublisherBridge


class ContentEngineService:
    APPROVABLE = frozenset({"draft", "pending_approval"})
    REJECTABLE = frozenset({"draft", "pending_approval"})
    QUEUEABLE = frozenset({"approved"})
    PUBLISHABLE = frozenset({"approved", "queued", "failed"})

    def __init__(
        self,
        repository: ContentEngineRepository,
        publisher: ContentPublisherBridge | None = None,
    ) -> None:
        self._repo = repository
        self._publisher = publisher or ContentPublisherBridge()

    def save(self, piece: ContentPiece) -> ContentPiece:
        return self._repo.save(piece)

    def get(self, tenant_id: str, content_id: str) -> ContentPiece:
        row = self._repo.get(tenant_id, content_id)
        if row is None:
            raise ContentNotFound(f"Contenido no encontrado: {content_id}")
        return row

    def list_content(
        self,
        tenant_id: str,
        *,
        status: str | None = None,
        statuses: tuple[str, ...] | None = None,
        campaign_id: str | None = None,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[ContentPiece]:
        return self._repo.list_content(
            tenant_id,
            status=status,
            statuses=statuses,
            campaign_id=campaign_id,
            brand_id=brand_id,
            limit=limit,
        )

    def list_publish_queue(self, tenant_id: str, *, limit: int = 50) -> list[ContentPiece]:
        return self._repo.list_content(
            tenant_id,
            statuses=tuple(PUBLISH_QUEUE_STATUSES),
            limit=limit,
        )

    def list_history(self, tenant_id: str, content_id: str, *, limit: int = 50) -> list[dict]:
        self.get(tenant_id, content_id)
        return self._repo.list_history(tenant_id, content_id, limit=limit)

    def update_fields(self, tenant_id: str, content_id: str, **fields: Any) -> ContentPiece:
        row = self.get(tenant_id, content_id)
        allowed = {
            "title", "headline", "body", "call_to_action", "status",
            "content_type", "flyer_ref", "explain", "llm_enrichment", "llm_skipped",
        }
        updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
        if "status" in updates and updates["status"] not in CONTENT_STATUSES:
            raise ContentInvalidStatus(f"Estado no válido: {updates['status']}")
        updated = replace(row, **updates, updated_at=_utc_now())
        return self._repo.save(updated)

    def approve(self, tenant_id: str, content_id: str, *, actor_id: str = "system") -> ContentPiece:
        row = self.get(tenant_id, content_id)
        if row.status not in self.APPROVABLE:
            raise ContentInvalidStatus(f"No se puede aprobar contenido en estado {row.status}")
        now = _utc_now()
        saved = self._repo.save(
            replace(
                row,
                status="approved",
                approved_by=actor_id,
                approved_at=now,
                rejected_reason="",
                error_message="",
                updated_at=now,
            )
        )
        self._repo.append_history(
            tenant_id, content_id, "approved", actor_id=actor_id,
            payload={"campaign_id": row.campaign_id, "channel": row.channel},
        )
        return saved

    def reject(
        self,
        tenant_id: str,
        content_id: str,
        *,
        reason: str = "",
        actor_id: str = "system",
    ) -> ContentPiece:
        row = self.get(tenant_id, content_id)
        if row.status not in self.REJECTABLE:
            raise ContentInvalidStatus(f"No se puede rechazar contenido en estado {row.status}")
        saved = self._repo.save(
            replace(
                row,
                status="rejected",
                rejected_reason=reason or "Rechazado",
                updated_at=_utc_now(),
            )
        )
        self._repo.append_history(
            tenant_id, content_id, "rejected", actor_id=actor_id,
            payload={"reason": reason, "campaign_id": row.campaign_id},
        )
        return saved

    def queue_for_publish(self, tenant_id: str, content_id: str, *, actor_id: str = "system") -> ContentPiece:
        row = self.get(tenant_id, content_id)
        if row.status not in self.QUEUEABLE:
            raise ContentInvalidStatus(
                f"Solo contenido aprobado puede ir a cola (estado actual: {row.status})"
            )
        post = self._publisher.enqueue_piece(row, tenant_id)
        post_id = post.get("id") or row.content_id
        saved = self._repo.save(
            replace(
                row,
                status="queued",
                publish_channel=row.channel,
                publish_status="queued",
                queue_post_id=post_id,
                error_message="",
                updated_at=_utc_now(),
            )
        )
        self._repo.append_history(
            tenant_id, content_id, "queued", actor_id=actor_id,
            payload={"queue_post_id": post_id, "channel": row.channel},
        )
        return saved

    def publish_now(
        self,
        tenant_id: str,
        content_id: str,
        *,
        actor_id: str = "system",
        dry_run: bool | None = None,
    ) -> tuple[ContentPiece, dict[str, Any]]:
        row = self.get(tenant_id, content_id)
        if row.status not in self.PUBLISHABLE:
            raise ContentInvalidStatus(
                f"Solo contenido aprobado o en cola puede publicarse (estado: {row.status})"
            )

        working = row
        if working.status == "failed":
            working = self._repo.save(
                replace(
                    working,
                    status="queued",
                    error_message="",
                    publish_status="queued",
                    updated_at=_utc_now(),
                )
            )
        elif working.status == "approved":
            working = self.queue_for_publish(tenant_id, content_id, actor_id=actor_id)

        self._repo.append_history(
            tenant_id, content_id, "publish_started", actor_id=actor_id,
            payload={"dry_run": dry_run if dry_run is not None else self._publisher.config.dry_run},
        )
        working = self._repo.save(
            replace(working, status="publishing", publish_status="publishing", updated_at=_utc_now())
        )

        result = self._publisher.publish_piece(working, tenant_id, dry_run=dry_run)

        if result.get("ok"):
            saved = self._repo.save(
                replace(
                    working,
                    status="published",
                    publish_status="published" if not result.get("dry_run") else "dry_run",
                    published_at=result.get("published_at") or _utc_now(),
                    publish_result=result,
                    error_message="",
                    publish_channel=result.get("channel") or working.channel,
                    queue_post_id=result.get("queue_post_id") or working.queue_post_id,
                    updated_at=_utc_now(),
                )
            )
            self._repo.append_history(
                tenant_id, content_id, "published", actor_id=actor_id, payload=result,
            )
            return saved, result

        saved = self._repo.save(
            replace(
                working,
                status="failed",
                publish_status="failed",
                error_message=result.get("error_message") or "Error al publicar",
                publish_result=result,
                updated_at=_utc_now(),
            )
        )
        self._repo.append_history(
            tenant_id, content_id, "publish_failed", actor_id=actor_id, payload=result,
        )
        return saved, result

    def record_created(self, piece: ContentPiece, *, actor_id: str = "system") -> None:
        self._repo.append_history(
            piece.tenant_id,
            piece.content_id,
            "created",
            actor_id=actor_id,
            payload={"campaign_id": piece.campaign_id},
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_history_id() -> str:
    return f"cth_{secrets.token_hex(6)}"
