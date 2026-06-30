from __future__ import annotations


class OpportunityEngineError(Exception):
    code = "opportunity_engine_error"
    http_status = 400

    def __init__(self, code: str, message: str, *, http_status: int = 400) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


class OpportunityNotFound(OpportunityEngineError):
    def __init__(self, opportunity_id: str) -> None:
        super().__init__(
            "opportunity_not_found",
            f"Oportunidad no encontrada: {opportunity_id}",
            http_status=404,
        )


class InvalidOpportunityTransition(OpportunityEngineError):
    def __init__(self, opportunity_id: str, status: str, action: str) -> None:
        super().__init__(
            "invalid_opportunity_transition",
            f"No se puede {action} oportunidad {opportunity_id} en estado {status}",
            http_status=409,
        )
