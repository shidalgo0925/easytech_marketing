"""Publish safety flags — VS2."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class PublishConfig:
    publish_enabled: bool = True
    linkedin_enabled: bool = True
    dry_run: bool = False

    @classmethod
    def from_env(cls) -> PublishConfig:
        return cls(
            publish_enabled=_env_bool("ACCIO_PUBLISH_ENABLED", default=True),
            linkedin_enabled=_env_bool("ACCIO_LINKEDIN_PUBLISH_ENABLED", default=True),
            dry_run=_env_bool("ACCIO_PUBLISH_DRY_RUN", default=False),
        )

    def explain_block(self, channel: str = "linkedin") -> str | None:
        if not self.publish_enabled:
            return "Publicación deshabilitada (ACCIO_PUBLISH_ENABLED=false)"
        if channel == "linkedin" and not self.linkedin_enabled:
            return "LinkedIn deshabilitado (ACCIO_LINKEDIN_PUBLISH_ENABLED=false)"
        return None
