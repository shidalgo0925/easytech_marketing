"""SQLite repository — Content Engine."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.content_engine_domain.engine_service import new_history_id
from Motor_Tecnico.accio_engine.content_engine_domain.model import ContentPiece
from Motor_Tecnico.accio_engine.content_engine_infrastructure.engine_mapper import piece_to_row, row_to_piece
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection

_INSERT = """
INSERT INTO content_pieces (
  tenant_id, content_id, campaign_id, recommendation_id, brand_id, title, format,
  channel, content_type, status, headline, body, call_to_action, hashtags_json,
  flyer_ref, objective, explain_json, llm_enrichment_json, llm_skipped,
  planner_version, builder_version, payload_json, created_at, updated_at,
  approved_by, approved_at, rejected_reason, publish_channel, publish_status,
  published_at, publish_result_json, error_message, queue_post_id
) VALUES (
  :tenant_id, :content_id, :campaign_id, :recommendation_id, :brand_id, :title, :format,
  :channel, :content_type, :status, :headline, :body, :call_to_action, :hashtags_json,
  :flyer_ref, :objective, :explain_json, :llm_enrichment_json, :llm_skipped,
  :planner_version, :builder_version, :payload_json, :created_at, :updated_at,
  :approved_by, :approved_at, :rejected_reason, :publish_channel, :publish_status,
  :published_at, :publish_result_json, :error_message, :queue_post_id
)
ON CONFLICT(tenant_id, content_id) DO UPDATE SET
  campaign_id=excluded.campaign_id, recommendation_id=excluded.recommendation_id,
  brand_id=excluded.brand_id, title=excluded.title, format=excluded.format,
  channel=excluded.channel, content_type=excluded.content_type, status=excluded.status,
  headline=excluded.headline, body=excluded.body, call_to_action=excluded.call_to_action,
  hashtags_json=excluded.hashtags_json, flyer_ref=excluded.flyer_ref, objective=excluded.objective,
  explain_json=excluded.explain_json, llm_enrichment_json=excluded.llm_enrichment_json,
  llm_skipped=excluded.llm_skipped, planner_version=excluded.planner_version,
  builder_version=excluded.builder_version, payload_json=excluded.payload_json,
  approved_by=excluded.approved_by, approved_at=excluded.approved_at,
  rejected_reason=excluded.rejected_reason, publish_channel=excluded.publish_channel,
  publish_status=excluded.publish_status, published_at=excluded.published_at,
  publish_result_json=excluded.publish_result_json, error_message=excluded.error_message,
  queue_post_id=excluded.queue_post_id, updated_at=excluded.updated_at
"""


class SqliteContentEngineRepository:
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

    def save(self, piece: ContentPiece) -> ContentPiece:
        conn = self._conn()
        try:
            conn.execute(_INSERT, piece_to_row(piece))
            conn.commit()
            return piece
        finally:
            if self._external is None:
                conn.close()

    def get(self, tenant_id: str, content_id: str) -> ContentPiece | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM content_pieces WHERE tenant_id = ? AND content_id = ?",
                (tenant_id, content_id),
            ).fetchone()
            return row_to_piece(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def list_content(
        self,
        tenant_id: str,
        *,
        status: str | None = None,
        statuses: tuple[str, ...] | None = None,
        campaign_id: str | None = None,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[ContentPiece]:
        conn = self._conn()
        try:
            sql = "SELECT * FROM content_pieces WHERE tenant_id = ?"
            params: list = [tenant_id]
            if status:
                sql += " AND status = ?"
                params.append(status)
            elif statuses:
                placeholders = ",".join("?" * len(statuses))
                sql += f" AND status IN ({placeholders})"
                params.extend(statuses)
            if campaign_id:
                sql += " AND campaign_id = ?"
                params.append(campaign_id)
            if brand_id:
                sql += " AND brand_id = ?"
                params.append(brand_id)
            sql += " ORDER BY updated_at DESC LIMIT ?"
            params.append(max(1, min(limit, 100)))
            return [row_to_piece(r) for r in conn.execute(sql, params).fetchall()]
        finally:
            if self._external is None:
                conn.close()

    def append_history(
        self,
        tenant_id: str,
        content_id: str,
        event_type: str,
        *,
        actor_id: str = "system",
        payload: dict | None = None,
    ) -> None:
        conn = self._conn()
        try:
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO content_history (
                  history_id, tenant_id, content_id, event_type, actor_id, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_history_id(),
                    tenant_id,
                    content_id,
                    event_type,
                    actor_id,
                    json.dumps(payload or {}, ensure_ascii=False),
                    now,
                ),
            )
            conn.commit()
        finally:
            if self._external is None:
                conn.close()

    def list_history(self, tenant_id: str, content_id: str, *, limit: int = 50) -> list[dict]:
        conn = self._conn()
        try:
            rows = conn.execute(
                """
                SELECT history_id, event_type, actor_id, payload_json, created_at
                FROM content_history
                WHERE tenant_id = ? AND content_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (tenant_id, content_id, max(1, min(limit, 100))),
            ).fetchall()
            out = []
            for row in rows:
                out.append(
                    {
                        "history_id": row["history_id"],
                        "event_type": row["event_type"],
                        "actor_id": row["actor_id"],
                        "payload": json.loads(row["payload_json"] or "{}"),
                        "created_at": row["created_at"],
                    }
                )
            return out
        finally:
            if self._external is None:
                conn.close()
