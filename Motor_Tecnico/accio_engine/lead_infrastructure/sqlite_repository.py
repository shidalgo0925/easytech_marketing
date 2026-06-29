"""SQLite adapter — leads table."""

from __future__ import annotations

import sqlite3

from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection
from Motor_Tecnico.accio_engine.lead_domain.model import Lead
from Motor_Tecnico.accio_engine.lead_infrastructure.legacy_mapper import (
    catalog_to_leads,
    lead_to_row,
    legacy_row_to_lead,
    leads_to_catalog,
    row_to_lead,
)


class SqliteLeadRepository:
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

    def load_catalog(self, tenant_id: str) -> dict:
        return leads_to_catalog(self._list_all(tenant_id))

    def save_catalog(self, tenant_id: str, data: dict) -> None:
        leads = catalog_to_leads(tenant_id, data)
        self._save_all(tenant_id, leads)

    def list_leads(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[Lead]:
        conn = self._conn()
        try:
            sql = "SELECT * FROM leads WHERE tenant_id = ?"
            params: list[str | int] = [tenant_id]
            if brand_id:
                sql += " AND brand_id = ?"
                params.append(brand_id)
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return [row_to_lead(r) for r in rows]
        finally:
            if self._external is None:
                conn.close()

    def get_lead(self, tenant_id: str, lead_id: str) -> Lead | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM leads WHERE tenant_id = ? AND lead_id = ?",
                (tenant_id, lead_id),
            ).fetchone()
            return row_to_lead(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def append_lead(self, tenant_id: str, entry: dict) -> Lead:
        lead = legacy_row_to_lead(tenant_id, entry)
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT INTO leads (
                  tenant_id, lead_id, brand_id, source, medium, channel,
                  campaign_id, landing_url, status, crm_destination, crm_lead_id,
                  contact_json, payload_json, created_at, updated_at
                ) VALUES (
                  :tenant_id, :lead_id, :brand_id, :source, :medium, :channel,
                  :campaign_id, :landing_url, :status, :crm_destination, :crm_lead_id,
                  :contact_json, :payload_json, :created_at, :updated_at
                )
                """,
                lead_to_row(lead),
            )
            conn.commit()
        finally:
            if self._external is None:
                conn.close()
        return lead

    def _list_all(self, tenant_id: str) -> list[Lead]:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM leads WHERE tenant_id = ? ORDER BY created_at DESC",
                (tenant_id,),
            ).fetchall()
            return [row_to_lead(r) for r in rows]
        finally:
            if self._external is None:
                conn.close()

    def _save_all(self, tenant_id: str, leads: list[Lead]) -> None:
        conn = self._conn()
        try:
            conn.execute("DELETE FROM leads WHERE tenant_id = ?", (tenant_id,))
            for lead in leads:
                conn.execute(
                    """
                    INSERT INTO leads (
                      tenant_id, lead_id, brand_id, source, medium, channel,
                      campaign_id, landing_url, status, crm_destination, crm_lead_id,
                      contact_json, payload_json, created_at, updated_at
                    ) VALUES (
                      :tenant_id, :lead_id, :brand_id, :source, :medium, :channel,
                      :campaign_id, :landing_url, :status, :crm_destination, :crm_lead_id,
                      :contact_json, :payload_json, :created_at, :updated_at
                    )
                    """,
                    lead_to_row(lead),
                )
            conn.commit()
        finally:
            if self._external is None:
                conn.close()

    def save_all_for_tenant(self, tenant_id: str, leads: list[Lead]) -> None:
        self._save_all(tenant_id, leads)
