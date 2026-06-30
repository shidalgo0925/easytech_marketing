from __future__ import annotations

from Motor_Tecnico.accio_engine.campaign_api.composition import build_campaign_engine_service
from Motor_Tecnico.accio_engine.campaign_infrastructure.application_adapters import CampaignRbacAdapter
from Motor_Tecnico.accio_engine.content_engine_application.use_cases import (
    ApproveContentPiece,
    CreateContentFromCampaign,
    EnrichContentPiece,
    GetContentExplain,
    GetContentHistory,
    GetContentPiece,
    ListContentPieces,
    ListContentPublishQueue,
    PatchContentPiece,
    PublishContentNow,
    QueueContentPiece,
    RejectContentPiece,
)
from Motor_Tecnico.accio_engine.content_engine_domain.engine_service import ContentEngineService
from Motor_Tecnico.accio_engine.content_engine_infrastructure.content_publisher_bridge import ContentPublisherBridge
from Motor_Tecnico.accio_engine.content_engine_infrastructure.engine_orchestrator import ContentEngineOrchestrator
from Motor_Tecnico.accio_engine.content_engine_infrastructure.engine_sqlite_repository import SqliteContentEngineRepository
from Motor_Tecnico.accio_engine.decision_engine_application.context import TenantContext
from Motor_Tecnico.accio_engine.memory_api.composition import get_memory_domain_service
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, memory_sql_enabled


def build_content_engine_service() -> ContentEngineService:
    ensure_schema()
    return ContentEngineService(
        SqliteContentEngineRepository(),
        ContentPublisherBridge(),
    )


def build_content_orchestrator() -> ContentEngineOrchestrator:
    return ContentEngineOrchestrator(
        build_content_engine_service(),
        build_campaign_engine_service(),
    )


def _memory_service() -> CorporateMemoryDomainService | None:
    if not memory_sql_enabled():
        return None
    try:
        return get_memory_domain_service()
    except Exception:
        return None


class ContentEngineUseCases:
    def __init__(self) -> None:
        engine = build_content_engine_service()
        orchestrator = build_content_orchestrator()
        auth = CampaignRbacAdapter()
        memory = _memory_service()
        self.list_content = ListContentPieces(engine, auth)
        self.list_queue = ListContentPublishQueue(engine, auth)
        self.get_content = GetContentPiece(engine, auth)
        self.from_campaign = CreateContentFromCampaign(orchestrator, auth)
        self.enrich_content = EnrichContentPiece(orchestrator, auth)
        self.patch_content = PatchContentPiece(engine, auth)
        self.approve_content = ApproveContentPiece(engine, auth, memory)
        self.reject_content = RejectContentPiece(engine, auth, memory)
        self.queue_content = QueueContentPiece(engine, auth, memory)
        self.publish_now = PublishContentNow(engine, auth, memory)
        self.get_history = GetContentHistory(engine, auth)
        self.get_explain = GetContentExplain(engine, auth)


_USE_CASES: ContentEngineUseCases | None = None


def content_engine_use_cases() -> ContentEngineUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = ContentEngineUseCases()
    return _USE_CASES


def reset_content_engine_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None


def tenant_context(tenant_id: str) -> TenantContext:
    return TenantContext(tenant_id=tenant_id)
