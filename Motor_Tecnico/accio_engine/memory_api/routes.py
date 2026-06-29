"""API v1 — Corporate Memory."""

from __future__ import annotations

from functools import wraps

from flask import request

from Motor_Tecnico.accio_engine.memory_api.composition import memory_use_cases, reset_memory_use_cases
from Motor_Tecnico.accio_engine.memory_api.dto import event_to_response
from Motor_Tecnico.accio_engine.memory_api.http_helpers import (
    error_response,
    http_status_for_application_error,
    success,
)
from Motor_Tecnico.accio_engine.memory_api.request_context import tenant_context
from Motor_Tecnico.accio_engine.memory_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.memory_application.query_inputs import (
    GetMemoryEventQuery,
    ListMemoryEventsQuery,
)


def reset_use_cases_cache() -> None:
    reset_memory_use_cases()


def _use_cases():
    return memory_use_cases()


def _handle_application_errors(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except ApplicationError as exc:
            return error_response(exc, http_status=http_status_for_application_error(exc))

    return wrapped


def _list_query_from_request() -> ListMemoryEventsQuery:
    args = request.args
    limit = int(args.get("limit", 50))
    offset = int(args.get("offset", 0))
    return ListMemoryEventsQuery(
        brand_id=args.get("brand_id") or None,
        event_type=args.get("event_type") or None,
        entity_type=args.get("entity_type") or None,
        entity_id=args.get("entity_id") or None,
        since=args.get("since") or None,
        until=args.get("until") or None,
        limit=limit,
        offset=offset,
    )


def register_memory_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/memory"

    @app.get(f"{base}/events")
    @auth_decorator
    @_handle_application_errors
    def api_list_memory_events(tenant_id: str):
        ctx = tenant_context(tenant_id)
        rows = _use_cases().list_events(ctx, _list_query_from_request())
        return success([event_to_response(row) for row in rows])

    @app.get(f"{base}/events/<event_id>")
    @auth_decorator
    @_handle_application_errors
    def api_get_memory_event(tenant_id: str, event_id: str):
        ctx = tenant_context(tenant_id)
        row = _use_cases().get_event(ctx, GetMemoryEventQuery(event_id=event_id))
        return success(event_to_response(row))
