"""SQLite adapter — campaigns table."""

from __future__ import annotations

import sqlite3

from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.campaign_infrastructure.legacy_mapper import (
    campaign_to_row,
    campaigns_to_store,
    row_to_campaign,
    store_to_campaigns,
)


class SqliteCampaignRepository:
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

    def load_store(self, tenant_id: str, brand_id: str) -> dict:
        campaigns = self.list_campaigns(tenant_id, brand_id)
        return campaigns_to_store(campaigns)

    def save_store(self, tenant_id: str, brand_id: str, data: dict) -> dict:
        campaigns = store_to_campaigns(tenant_id, brand_id, data)
        self._save_all(tenant_id, brand_id, campaigns)
        return campaigns_to_store(campaigns, meta={k: v for k, v in data.items() if k != "campaigns"})

    def list_campaigns(self, tenant_id: str, brand_id: str) -> list[Campaign]:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM campaigns WHERE tenant_id = ? AND brand_id = ? ORDER BY name COLLATE NOCASE",
                (tenant_id, brand_id),
            ).fetchall()
            return [row_to_campaign(r) for r in rows]
        finally:
            if self._external is None:
                conn.close()

    def get_campaign(self, tenant_id: str, brand_id: str, campaign_id: str) -> Campaign | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM campaigns WHERE tenant_id = ? AND brand_id = ? AND campaign_id = ?",
                (tenant_id, brand_id, campaign_id),
            ).fetchone()
            return row_to_campaign(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def _save_all(self, tenant_id: str, brand_id: str, campaigns: list[Campaign]) -> None:
        conn = self._conn()
        try:
            conn.execute(
                "DELETE FROM campaigns WHERE tenant_id = ? AND brand_id = ?",
                (tenant_id, brand_id),
            )
            for campaign in campaigns:
                conn.execute(
                    """
                    INSERT INTO campaigns (
                      tenant_id, campaign_id, brand_id, name, post_id, product_ref,
                      channel, status, objective, start_at, end_at, payload_json,
                      created_at, updated_at
                    ) VALUES (
                      :tenant_id, :campaign_id, :brand_id, :name, :post_id, :product_ref,
                      :channel, :status, :objective, :start_at, :end_at, :payload_json,
                      :created_at, :updated_at
                    )
                    """,
                    campaign_to_row(campaign),
                )
            conn.commit()
        finally:
            if self._external is None:
                conn.close()

    def save_all_for_brand(self, tenant_id: str, brand_id: str, campaigns: list[Campaign]) -> None:
        self._save_all(tenant_id, brand_id, campaigns)
