from __future__ import annotations

from flask import jsonify

from Motor_Tecnico.accio_engine.company_brain_application.errors import ApplicationError


def success(data, *, status: int = 200):
    return jsonify({"ok": True, "data": data}), status


def error_response(exc: ApplicationError, *, http_status: int | None = None):
    status = http_status or exc.http_status
    return jsonify({"ok": False, "error": exc.code, "message": exc.message}), status
