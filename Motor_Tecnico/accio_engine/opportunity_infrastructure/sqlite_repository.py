"""SQLite adapter — opportunities table (Opportunity Engine F1)."""

from __future__ import annotations

import sqlite3
from dataclasses import replace

from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity
from Motor_Tecnico.accio_engine.opportunity_infrastructure.mapper import opportunity_to_row, row_to_opportunity
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection


class SqliteOpportunityRepository:
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

    def upsert(self, opportunity: Opportunity) -> tuple[Opportunity, bool]:
        conn = self._conn()
        created = False
        try:
            existing = conn.execute(
                "SELECT opportunity_id, detected_at FROM opportunities WHERE tenant_id = ? AND signal_key = ?",
                (opportunity.tenant_id, opportunity.signal_key),
            ).fetchone()
            if existing:
                updated = replace(
                    opportunity,
                    opportunity_id=existing["opportunity_id"],
                    detected_at=existing["detected_at"],
                )
            else:
                updated = opportunity
                created = True
            conn.execute(
                """
                INSERT INTO opportunities (
                  tenant_id, opportunity_id, signal_key, signal_type, brand_id,
                  title, description, sector, need, product_slug, channel, landing_url,
                  priority, status, confidence, score, reasoning_json, source, payload_json, detected_at, updated_at
                ) VALUES (
                  :tenant_id, :opportunity_id, :signal_key, :signal_type, :brand_id,
                  :title, :description, :sector, :need, :product_slug, :channel, :landing_url,
                  :priority, :status, :confidence, :score, :reasoning_json, :source, :payload_json, :detected_at, :updated_at
                )
                ON CONFLICT(tenant_id, signal_key) DO UPDATE SET
                  signal_type = excluded.signal_type,
                  brand_id = excluded.brand_id,
                  title = excluded.title,
                  description = excluded.description,
                  sector = excluded.sector,
                  need = excluded.need,
                  product_slug = excluded.product_slug,
                  channel = excluded.channel,
                  landing_url = excluded.landing_url,
                  priority = excluded.priority,
                  confidence = excluded.confidence,
                  score = excluded.score,
                  reasoning_json = excluded.reasoning_json,
                  source = excluded.source,
                  payload_json = excluded.payload_json,
                  updated_at = excluded.updated_at
                """,
                opportunity_to_row(updated),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM opportunities WHERE tenant_id = ? AND signal_key = ?",
                (opportunity.tenant_id, opportunity.signal_key),
            ).fetchone()
            return row_to_opportunity(row), created
        finally:
            if self._external is None:
                conn.close()

    def get(self, tenant_id: str, opportunity_id: str) -> Opportunity | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM opportunities WHERE tenant_id = ? AND opportunity_id = ?",
                (tenant_id, opportunity_id),
            ).fetchone()
            return row_to_opportunity(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def get_by_signal_key(self, tenant_id: str, signal_key: str) -> Opportunity | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM opportunities WHERE tenant_id = ? AND signal_key = ?",
                (tenant_id, signal_key),
            ).fetchone()
            return row_to_opportunity(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def list_opportunities(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Opportunity]:
        conn = self._conn()
        try:
            sql = "SELECT * FROM opportunities WHERE tenant_id = ?"
            params: list[object] = [tenant_id]
            if brand_id:
                sql += " AND brand_id = ?"
                params.append(brand_id)
            if status:
                sql += " AND status = ?"
                params.append(status)
            sql += " ORDER BY score DESC, detected_at DESC LIMIT ?"
            params.append(max(1, min(limit, 200)))
            rows = conn.execute(sql, params).fetchall()
            return [row_to_opportunity(row) for row in rows]
        finally:
            if self._external is None:
                conn.close()

    def update(self, opportunity: Opportunity) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """
                UPDATE opportunities SET
                  signal_type = :signal_type,
                  brand_id = :brand_id,
                  title = :title,
                  description = :description,
                  sector = :sector,
                  need = :need,
                  product_slug = :product_slug,
                  channel = :channel,
                  landing_url = :landing_url,
                  priority = :priority,
                  status = :status,
                  confidence = :confidence,
                  source = :source,
                  payload_json = :payload_json,
                  updated_at = :updated_at
                WHERE tenant_id = :tenant_id AND opportunity_id = :opportunity_id
                """,
                opportunity_to_row(opportunity),
            )
            if conn.total_changes == 0:
                raise ValueError(f"Opportunity not found for update: {opportunity.opportunity_id}")
            conn.commit()
        finally:
            if self._external is None:
                conn.close()
