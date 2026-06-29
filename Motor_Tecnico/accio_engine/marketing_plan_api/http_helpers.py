"""Envelope y errores HTTP — API Contract v1."""

from __future__ import annotations

import uuid
from typing import Any

from flask import jsonify, request

from Motor_Tecnico.accio_engine.marketing_plan_application.errors import ApplicationError


def correlation_id() -> str:
    header = (request.headers.get("X-Correlation-Id") or "").strip()
    return header or str(uuid.uuid4())


def success(data: Any, *, status: int = 200, extra_meta: dict[str, Any] | None = None):
    meta = {"correlation_id": correlation_id(), "api_version": "v1"}
    if extra_meta:
        meta.update(extra_meta)
    resp = jsonify({"data": data, "meta": meta})
    resp.status_code = status
    resp.headers["X-Correlation-Id"] = meta["correlation_id"]
    return resp


def error_response(exc: ApplicationError, *, http_status: int):
    meta = {"correlation_id": correlation_id(), "api_version": "v1"}
    body = {
        "error": {
            "code": exc.code if isinstance(exc.code, str) else exc.code.value,
            "message": exc.message,
            "details": (exc.domain_error.details if exc.domain_error else None),
            "source": exc.source,
        },
        "meta": meta,
    }
    resp = jsonify(body)
    resp.status_code = http_status
    resp.headers["X-Correlation-Id"] = meta["correlation_id"]
    return resp


def http_status_for_application_error(exc: ApplicationError) -> int:
    if exc.source == "auth":
        return 403
    code = exc.code if isinstance(exc.code, str) else exc.code.value
    mapping = {
        "PlanNotFound": 404,
        "Forbidden": 403,
        "ActivePlanResolutionRequired": 409,
        "InvalidStatusTransition": 409,
        "PlanCompleted": 409,
        "PlanNotEditable": 409,
        "InvalidDateRange": 422,
        "PlanNotDeclarative": 422,
        "ForbiddenField": 422,
        "StrategyTypeInvalid": 422,
        "BudgetInvalid": 422,
        "CurrencyInvalid": 422,
    }
    return mapping.get(str(code), 422)
