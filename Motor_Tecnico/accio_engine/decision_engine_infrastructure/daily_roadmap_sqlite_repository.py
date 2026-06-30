"""SQLite adapter — daily_roadmaps table (M10.4)."""

from __future__ import annotations

import sqlite3

from Motor_Tecnico.accio_engine.decision_engine_domain.model import DailyRoadmap
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.roadmap_mapper import roadmap_to_row, row_to_roadmap
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection


class SqliteDailyRoadmapRepository:
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

    def save(self, roadmap: DailyRoadmap) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT INTO daily_roadmaps (
                  tenant_id, roadmap_id, company_id, roadmap_date,
                  generated_at, generator_version, summary_json
                ) VALUES (
                  :tenant_id, :roadmap_id, :company_id, :roadmap_date,
                  :generated_at, :generator_version, :summary_json
                )
                """,
                roadmap_to_row(roadmap),
            )
            conn.commit()
        finally:
            if self._external is None:
                conn.close()

    def get_by_date(self, tenant_id: str, company_id: str, roadmap_date: str) -> DailyRoadmap | None:
        conn = self._conn()
        try:
            row = conn.execute(
                """
                SELECT * FROM daily_roadmaps
                WHERE tenant_id = ? AND company_id = ? AND roadmap_date = ?
                """,
                (tenant_id, company_id, roadmap_date),
            ).fetchone()
            return row_to_roadmap(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def get_by_id(self, tenant_id: str, roadmap_id: str) -> DailyRoadmap | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM daily_roadmaps WHERE tenant_id = ? AND roadmap_id = ?",
                (tenant_id, roadmap_id),
            ).fetchone()
            return row_to_roadmap(row) if row else None
        finally:
            if self._external is None:
                conn.close()
