from __future__ import annotations


class DecisionEngineError(Exception):
    code = "decision_engine_error"
    http_status = 400

    def __init__(self, code: str, message: str, *, http_status: int = 400) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


class RecommendationNotFound(DecisionEngineError):
    def __init__(self, recommendation_id: str) -> None:
        super().__init__(
            "recommendation_not_found",
            f"Recomendación no encontrada: {recommendation_id}",
            http_status=404,
        )


class DailyRoadmapNotFound(DecisionEngineError):
    def __init__(self, roadmap_date: str) -> None:
        super().__init__(
            "daily_roadmap_not_found",
            f"Roadmap no encontrado para la fecha: {roadmap_date}",
            http_status=404,
        )


class InvalidRecommendationTransition(DecisionEngineError):
    def __init__(self, recommendation_id: str, status: str, action: str) -> None:
        super().__init__(
            "invalid_recommendation_transition",
            f"No se puede {action} recomendación {recommendation_id} en estado {status}",
            http_status=409,
        )


class RejectionReasonRequired(DecisionEngineError):
    def __init__(self) -> None:
        super().__init__(
            "rejection_reason_required",
            "El rechazo exige un motivo (reason)",
            http_status=400,
        )


class SnoozeUntilRequired(DecisionEngineError):
    def __init__(self) -> None:
        super().__init__(
            "snooze_until_required",
            "Posponer exige fecha until (ISO-8601)",
            http_status=400,
        )
