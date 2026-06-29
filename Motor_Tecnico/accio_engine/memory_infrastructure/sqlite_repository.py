"""SQLite adapter — append-only memory_events."""

from __future__ import annotations

import sqlite3
from typing import Any

from Motor_Tecnico.accio_engine.memory_domain.model import MemoryEvent
from Motor_Tecnico.accio_engine.memory_domain.ports import MemoryRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection

from .serializer import event_to_row, row_to_event


class SqliteMemoryRepository:
    def __init__(self, connection: sqlite3.Connection | None = None) -> None:
        self._external = connection
        if connection is not None:
            ensure_schema(connection)

    def _conn(self) -> sqlite3.Connection:
        if self._external is not None:
            return self._external
        conn = get_connection()
        ensure_schema(conn)
        return conn

    def append(self, event: MemoryEvent) -> None:
        row = event_to_row(event)
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT INTO memory_events (
                  event_id, tenant_id, brand_id, event_type,
                  actor_type, actor_id, timestamp,
                  entity_refs_json, payload_json, summary, correlation_id
                ) VALUES (
                  :event_id, :tenant_id, :brand_id, :event_type,
                  :actor_type, :actor_id, :timestamp,
                  :entity_refs_json, :payload_json, :summary, :correlation_id
                )
                """,
                row,
            )
            conn.commit()
        finally:
            if self._external is None:
                conn.close()

    def get_by_id(self, tenant_id: str, event_id: str) -> MemoryEvent | None:
        conn = self._conn()
        try:
            row = conn.execute(
                """
                SELECT * FROM memory_events
                WHERE tenant_id = ? AND event_id = ?
                """,
                (tenant_id, event_id),
            ).fetchone()
            return row_to_event(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def list_events(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        event_type: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryEvent]:
        clauses = ["tenant_id = ?"]
        params: list[Any] = [tenant_id]
        if brand_id:
            clauses.append("brand_id = ?")
            params.append(brand_id)
        if event_type:
            clauses.append("event_type = ?")
            params.append(event_type)
        if since:
            clauses.append("timestamp >= ?")
            params.append(since)
        if until:
            clauses.append("timestamp <= ?")
            params.append(until)
        if entity_type and entity_id:
            clauses.append(
                "EXISTS (SELECT 1 FROM json_each(entity_refs_json) je "
                "WHERE json_extract(je.value, '$.type') = ? "
                "AND json_extract(je.value, '$.id') = ?)"
            )
            params.extend([entity_type, entity_id])
        elif entity_type:
            clauses.append(
                "EXISTS (SELECT 1 FROM json_each(entity_refs_json) je "
                "WHERE json_extract(je.value, '$.type') = ?)"
            )
            params.append(entity_type)

        sql = (
            f"SELECT * FROM memory_events WHERE {' AND '.join(clauses)} "
            f"ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        )
        params.extend([limit, offset])
        conn = self._conn()
        try:
            rows = conn.execute(sql, params).fetchall()
            return [row_to_event(r) for r in rows]
        finally:
            if self._external is None:
                conn.close()
