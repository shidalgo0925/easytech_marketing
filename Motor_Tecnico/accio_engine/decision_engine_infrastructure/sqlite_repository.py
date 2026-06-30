"""SQLite adapter — recommendations table (M10.3)."""

from __future__ import annotations

import sqlite3

from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.recommendation_mapper import (
    recommendation_to_row,
    row_to_recommendation,
)
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection


class SqliteRecommendationRepository:
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

    def save(self, recommendation: Recommendation) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT INTO recommendations (
                  tenant_id, recommendation_id, company_id, brand_id, roadmap_id,
                  title, description, action, reason, expected_roi,
                  priority, priority_score, owner_role, owner_id, due_at,
                  status, source, confidence, justification_refs_json, dependencies_json,
                  created_by, approved_by, rejected_by, executed_at, result_json,
                  created_at, updated_at
                ) VALUES (
                  :tenant_id, :recommendation_id, :company_id, :brand_id, :roadmap_id,
                  :title, :description, :action, :reason, :expected_roi,
                  :priority, :priority_score, :owner_role, :owner_id, :due_at,
                  :status, :source, :confidence, :justification_refs_json, :dependencies_json,
                  :created_by, :approved_by, :rejected_by, :executed_at, :result_json,
                  :created_at, :updated_at
                )
                """,
                recommendation_to_row(recommendation),
            )
            conn.commit()
        finally:
            if self._external is None:
                conn.close()

    def get(self, tenant_id: str, recommendation_id: str) -> Recommendation | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM recommendations WHERE tenant_id = ? AND recommendation_id = ?",
                (tenant_id, recommendation_id),
            ).fetchone()
            return row_to_recommendation(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def list_recommendations(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        status: str | None = None,
        owner_role: str | None = None,
        roadmap_id: str | None = None,
        limit: int = 50,
    ) -> list[Recommendation]:
        conn = self._conn()
        try:
            sql = "SELECT * FROM recommendations WHERE tenant_id = ?"
            params: list[str | int] = [tenant_id]
            if brand_id:
                sql += " AND brand_id = ?"
                params.append(brand_id)
            if status:
                sql += " AND status = ?"
                params.append(status)
            if owner_role:
                sql += " AND owner_role = ?"
                params.append(owner_role)
            if roadmap_id:
                sql += " AND roadmap_id = ?"
                params.append(roadmap_id)
            sql += " ORDER BY priority_score DESC, created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return [row_to_recommendation(r) for r in rows]
        finally:
            if self._external is None:
                conn.close()
