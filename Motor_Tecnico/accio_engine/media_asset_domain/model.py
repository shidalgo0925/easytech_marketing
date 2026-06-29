from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MediaAsset:
    tenant_id: str
    asset_id: str
    brand_id: str
    asset_type: str
    uri: str
    title: str = ""
    status: str = "available"
    flyer_num: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    @property
    def missing(self) -> bool:
        return self.status == "missing"

    @property
    def file_name(self) -> str:
        return self.uri.rsplit("/", 1)[-1] if self.uri else ""

    def to_api_dict(self) -> dict[str, Any]:
        row = {
            "asset_id": self.asset_id,
            "tenant_id": self.tenant_id,
            "brand_id": self.brand_id,
            "app_id": self.brand_id,
            "asset_type": self.asset_type,
            "type": self.asset_type,
            "uri": self.uri,
            "title": self.title,
            "status": self.status,
            "missing": self.missing,
            "flyer_num": self.flyer_num,
            "file": self.file_name,
            "url": f"/accio/assets/flyers/{self.file_name}" if self.file_name else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        for key, value in (self.payload or {}).items():
            if key not in row and value is not None:
                row[key] = value
        return row
