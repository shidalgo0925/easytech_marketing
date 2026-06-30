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
