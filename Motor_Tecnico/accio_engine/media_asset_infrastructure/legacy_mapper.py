"""Legacy flyers/manifest.json ↔ MediaAsset."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.media_asset_domain.model import MediaAsset

_META_KEYS = frozenset({"version", "updated", "base_dir", "relative_base", "note", "queue", "publisher", "contact"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _asset_id_for_flyer(num: int | None, file_name: str | None) -> str:
    if num is not None:
        return f"flyer_{int(num):02d}"
    stem = Path(file_name or "extra").stem
    return f"extra_{stem}"


def flyer_row_to_asset(tenant_id: str, row: dict[str, Any], *, asset_type: str = "flyer") -> MediaAsset:
    num = row.get("num")
    file_name = row.get("file")
    missing = row.get("status") == "missing" or not file_name
    uri = f"flyers/{file_name}" if file_name else ""
    now = _utc_now()
    payload = {k: v for k, v in row.items() if k not in {"num", "file", "topic", "status"} and v is not None}
    return MediaAsset(
        tenant_id=tenant_id,
        asset_id=_asset_id_for_flyer(num, file_name),
        brand_id=marketing_app.DEFAULT_APP_ID,
        asset_type=asset_type,
        uri=uri,
        title=str(row.get("topic") or file_name or ""),
        status="missing" if missing else "available",
        flyer_num=int(num) if num is not None else None,
        payload=payload,
        created_at=now,
        updated_at=now,
    )


def manifest_to_assets(tenant_id: str, manifest: dict[str, Any]) -> list[MediaAsset]:
    assets: list[MediaAsset] = []
    for row in manifest.get("flyers", []):
        assets.append(flyer_row_to_asset(tenant_id, row, asset_type="flyer"))
    for row in manifest.get("extras", []):
        assets.append(flyer_row_to_asset(tenant_id, row, asset_type="extra"))
    return assets


def assets_to_manifest(assets: list[MediaAsset], *, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    data = dict(meta or {})
    data.setdefault("version", 1)
    flyers: list[dict[str, Any]] = []
    extras: list[dict[str, Any]] = []
    for asset in assets:
        row = {
            "topic": asset.title,
            "file": asset.file_name or None,
        }
        if asset.flyer_num is not None:
            row["num"] = asset.flyer_num
        if asset.missing:
            row["status"] = "missing"
        if asset.payload:
            row.update(asset.payload)
        if asset.asset_type == "extra":
            extras.append(row)
        else:
            flyers.append(row)
    data["flyers"] = flyers
    data["extras"] = extras
    data["updated"] = _utc_now()[:10]
    return data


def asset_to_row(asset: MediaAsset) -> dict[str, Any]:
    return {
        "tenant_id": asset.tenant_id,
        "asset_id": asset.asset_id,
        "brand_id": asset.brand_id,
        "asset_type": asset.asset_type,
        "uri": asset.uri,
        "title": asset.title,
        "status": asset.status,
        "flyer_num": asset.flyer_num,
        "payload_json": json.dumps(asset.payload or {}, ensure_ascii=False),
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
    }


def row_to_asset(row: Any) -> MediaAsset:
    return MediaAsset(
        tenant_id=row["tenant_id"],
        asset_id=row["asset_id"],
        brand_id=row["brand_id"],
        asset_type=row["asset_type"],
        uri=row["uri"],
        title=row["title"] or "",
        status=row["status"],
        flyer_num=row["flyer_num"],
        payload=json.loads(row["payload_json"] or "{}"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
