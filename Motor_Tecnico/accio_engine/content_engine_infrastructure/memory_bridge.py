"""Corporate Memory events — Content Engine (VS2)."""

from __future__ import annotations

from typing import Any

from Motor_Tecnico.accio_engine.content_engine_domain.model import ContentPiece
from Motor_Tecnico.accio_engine.memory_domain.model import Actor, EntityRef, MemoryEvent
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService


def _actor(actor_id: str) -> Actor:
    kind = "system" if actor_id in {"system", "api_key", "api"} else "user"
    return Actor(type=kind, id=actor_id)


def _refs(piece: ContentPiece) -> tuple[EntityRef, ...]:
    refs = [EntityRef(type="ContentPiece", id=piece.content_id)]
    if piece.campaign_id:
        refs.append(EntityRef(type="Campaign", id=piece.campaign_id))
    if piece.brand_id:
        refs.append(EntityRef(type="Brand", id=piece.brand_id))
    return tuple(refs)


def _record(
    memory: CorporateMemoryDomainService | None,
    *,
    piece: ContentPiece,
    event_type: str,
    actor_id: str,
    summary: str,
    payload: dict[str, Any],
) -> None:
    if memory is None:
        return
    memory.record(
        MemoryEvent(
            event_id="",
            tenant_id=piece.tenant_id,
            brand_id=piece.brand_id,
            event_type=event_type,
            actor=_actor(actor_id),
            timestamp="",
            entity_refs=_refs(piece),
            payload=payload,
            summary=summary,
        )
    )


def record_content_approved(
    memory: CorporateMemoryDomainService | None,
    *,
    piece: ContentPiece,
    actor_id: str,
) -> None:
    _record(
        memory,
        piece=piece,
        event_type="ContentApproved",
        actor_id=actor_id,
        summary=f"Contenido aprobado: {piece.title}",
        payload={
            "content_id": piece.content_id,
            "campaign_id": piece.campaign_id,
            "channel": piece.channel,
            "status": piece.status,
        },
    )


def record_content_rejected(
    memory: CorporateMemoryDomainService | None,
    *,
    piece: ContentPiece,
    actor_id: str,
    reason: str,
) -> None:
    _record(
        memory,
        piece=piece,
        event_type="ContentRejected",
        actor_id=actor_id,
        summary=f"Contenido rechazado: {piece.title}",
        payload={
            "content_id": piece.content_id,
            "campaign_id": piece.campaign_id,
            "channel": piece.channel,
            "reason": reason,
        },
    )


def record_content_queued(
    memory: CorporateMemoryDomainService | None,
    *,
    piece: ContentPiece,
    actor_id: str,
    queue_post_id: str,
) -> None:
    _record(
        memory,
        piece=piece,
        event_type="ContentQueued",
        actor_id=actor_id,
        summary=f"Contenido en cola: {piece.title}",
        payload={
            "content_id": piece.content_id,
            "campaign_id": piece.campaign_id,
            "channel": piece.channel,
            "queue_post_id": queue_post_id,
        },
    )


def record_content_publish_started(
    memory: CorporateMemoryDomainService | None,
    *,
    piece: ContentPiece,
    actor_id: str,
    dry_run: bool,
) -> None:
    _record(
        memory,
        piece=piece,
        event_type="ContentPublishStarted",
        actor_id=actor_id,
        summary=f"Publicación iniciada: {piece.title}",
        payload={
            "content_id": piece.content_id,
            "campaign_id": piece.campaign_id,
            "channel": piece.channel,
            "dry_run": dry_run,
        },
    )


def record_content_published(
    memory: CorporateMemoryDomainService | None,
    *,
    piece: ContentPiece,
    actor_id: str,
    result: dict[str, Any],
) -> None:
    _record(
        memory,
        piece=piece,
        event_type="ContentPublished",
        actor_id=actor_id,
        summary=f"Contenido publicado: {piece.title}",
        payload={
            "content_id": piece.content_id,
            "campaign_id": piece.campaign_id,
            "channel": piece.channel,
            "dry_run": result.get("dry_run", False),
            "external_post_id": result.get("external_post_id"),
            "external_url": result.get("external_url"),
        },
    )


def record_content_publish_failed(
    memory: CorporateMemoryDomainService | None,
    *,
    piece: ContentPiece,
    actor_id: str,
    error_message: str,
    result: dict[str, Any] | None = None,
) -> None:
    _record(
        memory,
        piece=piece,
        event_type="ContentPublishFailed",
        actor_id=actor_id,
        summary=f"Fallo al publicar: {piece.title}",
        payload={
            "content_id": piece.content_id,
            "campaign_id": piece.campaign_id,
            "channel": piece.channel,
            "error_message": error_message,
            "result": result or {},
        },
    )
