"""SQLite platform database — Marketing OS M0+."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from .schema_v2_company_brain import _COMPANY_PROFILES_DDL
from .schema_v3_brands import _BRANDS_DDL
from .schema_v4_publications import _PUBLICATIONS_DDL
from .schema_v5_products import _PRODUCTS_DDL
from .schema_v6_knowledge import _KNOWLEDGE_ARTICLES_DDL
from .schema_v7_campaigns import _CAMPAIGNS_DDL
from .schema_v8_media_assets import _MEDIA_ASSETS_DDL
from .schema_v9_leads import _LEADS_DDL
from .schema_v10_recommendations import _RECOMMENDATIONS_DDL
from .schema_v11_daily_roadmaps import _DAILY_ROADMAPS_DDL
from .schema_v12_opportunities import _OPPORTUNITIES_DDL
from .schema_v13_intelligence import apply_schema_v13
from .schema_v14_campaign_engine import apply_schema_v14

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_DB_PATH = BASE_DIR / "Marketing" / "platform" / "marketing_os.db"

_MEMORY_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS memory_events (
  event_id        TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT,
  event_type      TEXT NOT NULL,
  actor_type      TEXT NOT NULL,
  actor_id        TEXT,
  timestamp       TEXT NOT NULL,
  entity_refs_json TEXT NOT NULL,
  payload_json    TEXT,
  summary         TEXT,
  correlation_id  TEXT
);

CREATE INDEX IF NOT EXISTS idx_memory_tenant_time
  ON memory_events(tenant_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_memory_tenant_type
  ON memory_events(tenant_id, event_type);

CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);
"""

_SCHEMA_SCRIPTS: dict[int, str] = {
    1: _MEMORY_EVENTS_DDL,
    2: _COMPANY_PROFILES_DDL,
    3: _BRANDS_DDL,
    4: _PUBLICATIONS_DDL,
    5: _PRODUCTS_DDL,
    6: _KNOWLEDGE_ARTICLES_DDL,
    7: _CAMPAIGNS_DDL,
    8: _MEDIA_ASSETS_DDL,
    9: _LEADS_DDL,
    10: _RECOMMENDATIONS_DDL,
    11: _DAILY_ROADMAPS_DDL,
    12: _OPPORTUNITIES_DDL,
    13: "",
    14: "",
}


def get_db_path() -> Path:
    raw = os.environ.get("ACCIO_PLATFORM_DB", "").strip()
    if raw:
        return Path(raw)
    return DEFAULT_DB_PATH


def memory_store_mode() -> str:
    """off | sql | dual — default sql after M0."""
    return os.environ.get("ACCIO_MEMORY_STORE", "sql").strip().lower() or "sql"


def memory_sql_enabled() -> bool:
    return memory_store_mode() in {"sql", "dual"}


def brain_store_mode() -> str:
    """json | sql | dual — default json until migrated."""
    return os.environ.get("ACCIO_BRAIN_STORE", "json").strip().lower() or "json"


def brain_sql_enabled() -> bool:
    return brain_store_mode() in {"sql", "dual"}


def brain_json_enabled() -> bool:
    return brain_store_mode() in {"json", "dual"}


def brand_store_mode() -> str:
    """json | sql | dual — default json until migrated."""
    return os.environ.get("ACCIO_BRAND_STORE", "json").strip().lower() or "json"


def brand_sql_enabled() -> bool:
    return brand_store_mode() in {"sql", "dual"}


def brand_json_enabled() -> bool:
    return brand_store_mode() in {"json", "dual"}


def publication_store_mode() -> str:
    """json | sql | dual — default json until migrated."""
    return os.environ.get("ACCIO_PUBLICATION_STORE", "json").strip().lower() or "json"


def publication_sql_enabled() -> bool:
    return publication_store_mode() in {"sql", "dual"}


def publication_json_enabled() -> bool:
    return publication_store_mode() in {"json", "dual"}


def product_store_mode() -> str:
    """json | sql | dual — default json until migrated."""
    return os.environ.get("ACCIO_PRODUCT_STORE", "json").strip().lower() or "json"


def product_sql_enabled() -> bool:
    return product_store_mode() in {"sql", "dual"}


def product_json_enabled() -> bool:
    return product_store_mode() in {"json", "dual"}


def knowledge_store_mode() -> str:
    """json | sql | dual — default json until migrated."""
    return os.environ.get("ACCIO_KNOWLEDGE_STORE", "json").strip().lower() or "json"


def knowledge_sql_enabled() -> bool:
    return knowledge_store_mode() in {"sql", "dual"}


def knowledge_json_enabled() -> bool:
    return knowledge_store_mode() in {"json", "dual"}


def campaign_store_mode() -> str:
    """json | sql | dual — default json until migrated."""
    return os.environ.get("ACCIO_CAMPAIGN_STORE", "json").strip().lower() or "json"


def campaign_sql_enabled() -> bool:
    return campaign_store_mode() in {"sql", "dual"}


def campaign_json_enabled() -> bool:
    return campaign_store_mode() in {"json", "dual"}


def asset_store_mode() -> str:
    """json | sql | dual — default json until migrated."""
    return os.environ.get("ACCIO_ASSET_STORE", "json").strip().lower() or "json"


def asset_sql_enabled() -> bool:
    return asset_store_mode() in {"sql", "dual"}


def asset_json_enabled() -> bool:
    return asset_store_mode() in {"json", "dual"}


def lead_store_mode() -> str:
    """json | sql | dual — default json until migrated."""
    return os.environ.get("ACCIO_LEAD_STORE", "json").strip().lower() or "json"


def lead_sql_enabled() -> bool:
    return lead_store_mode() in {"sql", "dual"}


def lead_json_enabled() -> bool:
    return lead_store_mode() in {"json", "dual"}


def get_connection(*, readonly: bool = False) -> sqlite3.Connection:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    uri = f"file:{path}?mode={'ro' if readonly else 'rwc'}"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_schema(conn: sqlite3.Connection | None = None) -> None:
    own = conn is None
    if own:
        conn = get_connection()
    try:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        for version in sorted(_SCHEMA_SCRIPTS):
            script = _SCHEMA_SCRIPTS[version]
            if script:
                conn.executescript(script)
            if version == 13:
                apply_schema_v13(conn)
            if version == 14:
                apply_schema_v14(conn)
            row = conn.execute(
                "SELECT version FROM schema_migrations WHERE version = ?",
                (version,),
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (version, now),
                )
        conn.commit()
    finally:
        if own:
            conn.close()
