from __future__ import annotations

CAMPAIGN_ENGINE_VERSION = "campaign_engine_v1"
CAMPAIGN_PLANNER_VERSION = "campaign_planner_v1"
CAMPAIGN_BUILDER_VERSION = "campaign_builder_v1"
CAMPAIGN_EXPLAIN_VERSION = "campaign_explain_v1"

ENGINE_CAMPAIGN_STATUSES = frozenset(
    {
        "draft",
        "pending_approval",
        "approved",
        "scheduled",
        "running",
        "completed",
        "cancelled",
        "archived",
    }
)

LEGACY_CAMPAIGN_STATUSES = frozenset({"active", "inactive", "paused", "stopped"})
