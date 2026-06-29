"""SQLite adapter — publications table."""

from __future__ import annotations

import sqlite3

from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection
from Motor_Tecnico.accio_engine.publication_domain.model import Publication
from Motor_Tecnico.accio_engine.publication_infrastructure.legacy_mapper import (
    publication_to_row,
    publications_to_queue,
    queue_to_publications,
    row_to_publication,
)


class SqlitePublicationRepository:
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

    def load_queue(self, tenant_id: str, brand_id: str) -> dict:
        pubs = self.list_publications(tenant_id, brand_id)
        return publications_to_queue(pubs)

    def save_queue(self, tenant_id: str, brand_id: str, data: dict) -> None:
        pubs = queue_to_publications(tenant_id, brand_id, data)
        self._save_all(tenant_id, brand_id, pubs)

    def list_publications(
        self,
        tenant_id: str,
        brand_id: str,
        *,
        status: str | None = None,
    ) -> list[Publication]:
        conn = self._conn()
        try:
            sql = "SELECT * FROM publications WHERE tenant_id = ? AND brand_id = ?"
            params: list[str] = [tenant_id, brand_id]
            if status:
                sql += " AND status = ?"
                params.append(status.strip().lower())
            sql += " ORDER BY scheduled_at DESC, created_at DESC"
            rows = conn.execute(sql, params).fetchall()
            return [row_to_publication(r) for r in rows]
        finally:
            if self._external is None:
                conn.close()

    def get_publication(self, tenant_id: str, brand_id: str, publication_id: str) -> Publication | None:
        conn = self._conn()
        try:
            row = conn.execute(
                """
                SELECT * FROM publications
                WHERE tenant_id = ? AND brand_id = ?
                  AND (publication_id = ? OR legacy_queue_id = ?)
                """,
                (tenant_id, brand_id, publication_id, publication_id),
            ).fetchone()
            return row_to_publication(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def _save_all(self, tenant_id: str, brand_id: str, publications: list[Publication]) -> None:
        conn = self._conn()
        try:
            conn.execute(
                "DELETE FROM publications WHERE tenant_id = ? AND brand_id = ?",
                (tenant_id, brand_id),
            )
            for pub in publications:
                conn.execute(
                    """
                    INSERT INTO publications (
                      tenant_id, publication_id, brand_id, channel, title, body,
                      status, scheduled_at, published_at, external_post_id,
                      flyer_ref, campaign_id, legacy_queue_id, payload_json,
                      created_at, updated_at
                    ) VALUES (
                      :tenant_id, :publication_id, :brand_id, :channel, :title, :body,
                      :status, :scheduled_at, :published_at, :external_post_id,
                      :flyer_ref, :campaign_id, :legacy_queue_id, :payload_json,
                      :created_at, :updated_at
                    )
                    """,
                    publication_to_row(pub),
                )
            conn.commit()
        finally:
            if self._external is None:
                conn.close()

    def save_all_for_tenant(self, tenant_id: str, brand_id: str, publications: list[Publication]) -> None:
        self._save_all(tenant_id, brand_id, publications)
