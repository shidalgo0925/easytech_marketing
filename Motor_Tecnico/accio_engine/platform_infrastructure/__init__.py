"""Platform infrastructure — DB, shared adapters (Marketing OS M0)."""

from .db import ensure_schema, get_connection, get_db_path, memory_store_mode

__all__ = ["ensure_schema", "get_connection", "get_db_path", "memory_store_mode"]
