from __future__ import annotations

from Motor_Tecnico.accio_engine.campaign_application.errors import ApplicationError as CampaignApplicationError
from Motor_Tecnico.accio_engine.content_engine_domain.errors import ContentEngineError

ApplicationError = CampaignApplicationError


def from_content_error(exc: ContentEngineError) -> ApplicationError:
    return ApplicationError(exc.code, exc.message, exc.http_status)
