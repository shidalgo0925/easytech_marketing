from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.content_engine_domain.errors import ContentEngineError, ContentInvalidStatus, ContentNotFound
from Motor_Tecnico.accio_engine.content_engine_domain.model import ContentPiece
from Motor_Tecnico.accio_engine.content_engine_domain.ports import ContentEngineRepository
from Motor_Tecnico.accio_engine.content_engine_domain.constants import CONTENT_STATUSES


class ContentEngineService:
    APPROVABLE = frozenset({"draft", "pending_approval"})

    def __init__(self, repository: ContentEngineRepository) -> None:
        self._repo = repository

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
        campaign_id: str | None = None,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[ContentPiece]:
        return self._repo.list_content(
            tenant_id,
            status=status,
            campaign_id=campaign_id,
            brand_id=brand_id,
            limit=limit,
        )

    def update_fields(self, tenant_id: str, content_id: str, **fields: Any) -> ContentPiece:
        from dataclasses import replace

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
        from dataclasses import replace

        saved = self._repo.save(replace(row, status="approved", updated_at=_utc_now()))
        self._repo.append_history(tenant_id, content_id, "approved", actor_id=actor_id)
        return saved

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
