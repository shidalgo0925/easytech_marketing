"""SQLite adapter — company_profiles."""

from __future__ import annotations

import sqlite3

from Motor_Tecnico.accio_engine.company_brain_domain.model import CompanyBrain
from Motor_Tecnico.accio_engine.company_brain_domain.ports import CompanyBrainRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection

from .legacy_mapper import brain_to_row, row_to_brain


class SqliteCompanyBrainRepository:
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

    def get(self, tenant_id: str) -> CompanyBrain | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM company_profiles WHERE tenant_id = ?",
                (tenant_id,),
            ).fetchone()
            return row_to_brain(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def save(self, brain: CompanyBrain) -> None:
        row = brain_to_row(brain)
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT INTO company_profiles (
                  tenant_id, company_id, profile_json, status,
                  valid_from, source, last_synced_at, updated_at
                ) VALUES (
                  :tenant_id, :company_id, :profile_json, :status,
                  :valid_from, :source, :last_synced_at, :updated_at
                )
                ON CONFLICT(tenant_id) DO UPDATE SET
                  company_id = excluded.company_id,
                  profile_json = excluded.profile_json,
                  status = excluded.status,
                  valid_from = excluded.valid_from,
                  source = excluded.source,
                  last_synced_at = excluded.last_synced_at,
                  updated_at = excluded.updated_at
                """,
                row,
            )
            conn.commit()
        finally:
            if self._external is None:
                conn.close()
