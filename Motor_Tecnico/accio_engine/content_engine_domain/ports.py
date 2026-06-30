from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.content_engine_domain.model import ContentPiece


class ContentEngineRepository(Protocol):
    def save(self, piece: ContentPiece) -> ContentPiece:
        ...

    def get(self, tenant_id: str, content_id: str) -> ContentPiece | None:
        ...

    def list_content(
        self,
        tenant_id: str,
        *,
        status: str | None = None,
        campaign_id: str | None = None,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[ContentPiece]:
        ...

    def append_history(
        self,
        tenant_id: str,
        content_id: str,
        event_type: str,
        *,
        actor_id: str = "system",
        payload: dict | None = None,
    ) -> None:
        ...
