"""Platform infrastructure — DB, shared adapters (Marketing OS M0+)."""

from .db import (
    brain_json_enabled,
    brain_sql_enabled,
    brain_store_mode,
    brand_json_enabled,
    brand_sql_enabled,
    brand_store_mode,
    ensure_schema,
    get_connection,
    get_db_path,
    memory_store_mode,
    memory_sql_enabled,
)

__all__ = [
    "brain_json_enabled",
    "brain_sql_enabled",
    "brain_store_mode",
    "brand_json_enabled",
    "brand_sql_enabled",
    "brand_store_mode",
    "ensure_schema",
    "get_connection",
    "get_db_path",
    "memory_store_mode",
    "memory_sql_enabled",
]
