from __future__ import annotations

from Motor_Tecnico.accio_engine.campaign_domain.errors import CampaignError


class ApplicationError(Exception):
    def __init__(self, code: str, message: str, http_status: int = 400) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)

    @classmethod
    def from_domain(cls, exc: CampaignError) -> ApplicationError:
        return cls(exc.code, exc.message, exc.http_status)
