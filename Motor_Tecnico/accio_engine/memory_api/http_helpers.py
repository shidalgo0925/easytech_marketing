"""HTTP helpers — align with marketing_plan_api style."""

from __future__ import annotations

from flask import jsonify

from Motor_Tecnico.accio_engine.memory_application.errors import ApplicationError


def success(data, *, status: int = 200):
    return jsonify({"ok": True, "data": data}), status


def error_response(exc: ApplicationError, *, http_status: int | None = None):
    status = http_status or exc.http_status
    return (
        jsonify({"ok": False, "error": exc.code, "message": exc.message}),
        status,
    )


def http_status_for_application_error(exc: ApplicationError) -> int:
    return exc.http_status
