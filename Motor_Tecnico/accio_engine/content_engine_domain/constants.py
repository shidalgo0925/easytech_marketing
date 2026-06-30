from __future__ import annotations

CONTENT_ENGINE_VERSION = "content_engine_v1"
CONTENT_PLANNER_VERSION = "content_planner_v1"
CONTENT_BUILDER_VERSION = "content_builder_v1"
CONTENT_EXPLAIN_VERSION = "content_explain_v1"

CONTENT_STATUSES = frozenset(
    {
        "draft",
        "pending_approval",
        "approved",
        "scheduled",
        "published",
        "archived",
        "cancelled",
    }
)

CONTENT_FORMATS = frozenset({"post", "article", "carousel", "email", "whatsapp", "script"})
