"""SQLite repository — Campaign Engine (tenant-scoped CRUD)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.campaign_domain.engine_service import new_history_id
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.campaign_infrastructure.engine_mapper import campaign_to_row, row_to_campaign
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection

_INSERT_SQL = """
INSERT INTO campaigns (
  tenant_id, campaign_id, brand_id, name, post_id, product_ref, channel, status,
  objective, start_at, end_at, payload_json, created_at, updated_at,
  recommendation_id, opportunity_id, description, target_audience, value_proposition,
  call_to_action, priority, owner, start_date, end_date, budget, estimated_reach,
  estimated_leads, estimated_conversion, campaign_type, frequency, channels_json,
  kpis_json, explain_json, llm_enrichment_json, llm_skipped, planner_version,
  builder_version, origin_score
) VALUES (
  :tenant_id, :campaign_id, :brand_id, :name, :post_id, :product_ref, :channel, :status,
  :objective, :start_at, :end_at, :payload_json, :created_at, :updated_at,
  :recommendation_id, :opportunity_id, :description, :target_audience, :value_proposition,
  :call_to_action, :priority, :owner, :start_date, :end_date, :budget, :estimated_reach,
  :estimated_leads, :estimated_conversion, :campaign_type, :frequency, :channels_json,
  :kpis_json, :explain_json, :llm_enrichment_json, :llm_skipped, :planner_version,
  :builder_version, :origin_score
)
ON CONFLICT(tenant_id, campaign_id) DO UPDATE SET
  brand_id=excluded.brand_id, name=excluded.name, post_id=excluded.post_id,
  product_ref=excluded.product_ref, channel=excluded.channel, status=excluded.status,
  objective=excluded.objective, start_at=excluded.start_at, end_at=excluded.end_at,
  payload_json=excluded.payload_json, updated_at=excluded.updated_at,
  recommendation_id=excluded.recommendation_id, opportunity_id=excluded.opportunity_id,
  description=excluded.description, target_audience=excluded.target_audience,
  value_proposition=excluded.value_proposition, call_to_action=excluded.call_to_action,
  priority=excluded.priority, owner=excluded.owner, start_date=excluded.start_date,
  end_date=excluded.end_date, budget=excluded.budget, estimated_reach=excluded.estimated_reach,
  estimated_leads=excluded.estimated_leads, estimated_conversion=excluded.estimated_conversion,
  campaign_type=excluded.campaign_type, frequency=excluded.frequency,
  channels_json=excluded.channels_json, kpis_json=excluded.kpis_json,
  explain_json=excluded.explain_json, llm_enrichment_json=excluded.llm_enrichment_json,
  llm_skipped=excluded.llm_skipped, planner_version=excluded.planner_version,
  builder_version=excluded.builder_version, origin_score=excluded.origin_score
"""


class SqliteCampaignEngineRepository:
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

    def save(self, campaign: Campaign) -> Campaign:
        conn = self._conn()
        try:
            row = campaign_to_row(campaign)
            conn.execute(_INSERT_SQL, row)
            self._sync_channels(conn, campaign)
            self._sync_kpis(conn, campaign)
            conn.commit()
            return campaign
        finally:
            if self._external is None:
                conn.close()

    def get(self, tenant_id: str, campaign_id: str) -> Campaign | None:
        conn = self._conn()
        try:
            db_row = conn.execute(
                "SELECT * FROM campaigns WHERE tenant_id = ? AND campaign_id = ?",
                (tenant_id, campaign_id),
            ).fetchone()
            return row_to_campaign(db_row) if db_row else None
        finally:
            if self._external is None:
                conn.close()

    def list_campaigns(
        self,
        tenant_id: str,
        *,
        status: str | None = None,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[Campaign]:
        conn = self._conn()
        try:
            sql = "SELECT * FROM campaigns WHERE tenant_id = ?"
            params: list = [tenant_id]
            if status:
                sql += " AND status = ?"
                params.append(status)
            if brand_id:
                sql += " AND brand_id = ?"
                params.append(brand_id)
            sql += " ORDER BY updated_at DESC LIMIT ?"
            params.append(max(1, min(limit, 100)))
            rows = conn.execute(sql, params).fetchall()
            return [row_to_campaign(r) for r in rows]
        finally:
            if self._external is None:
                conn.close()

    def append_history(
        self,
        tenant_id: str,
        campaign_id: str,
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
                INSERT INTO campaign_history (
                  history_id, tenant_id, campaign_id, event_type, actor_id, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_history_id(),
                    tenant_id,
                    campaign_id,
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

    def _sync_channels(self, conn: sqlite3.Connection, campaign: Campaign) -> None:
        conn.execute(
            "DELETE FROM campaign_channels WHERE tenant_id = ? AND campaign_id = ?",
            (campaign.tenant_id, campaign.campaign_id),
        )
        for ch in campaign.channels:
            conn.execute(
                """
                INSERT INTO campaign_channels (tenant_id, campaign_id, channel, role, config_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    campaign.tenant_id,
                    campaign.campaign_id,
                    ch.channel,
                    ch.role,
                    json.dumps(ch.config or {}, ensure_ascii=False),
                ),
            )

    def _sync_kpis(self, conn: sqlite3.Connection, campaign: Campaign) -> None:
        conn.execute(
            "DELETE FROM campaign_kpis WHERE tenant_id = ? AND campaign_id = ?",
            (campaign.tenant_id, campaign.campaign_id),
        )
        for kpi in campaign.kpis:
            conn.execute(
                """
                INSERT INTO campaign_kpis (tenant_id, campaign_id, kpi_id, name, target_value, unit)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    campaign.tenant_id,
                    campaign.campaign_id,
                    kpi.kpi_id,
                    kpi.name,
                    kpi.target_value,
                    kpi.unit,
                ),
            )
