from __future__ import annotations

import json
from pathlib import Path

from Motor_Tecnico.accio_engine.knowledge_matrix_domain.model import (
    BrandDefault,
    KnowledgeMatrix,
    ProductMapping,
    SectorEntry,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


def _parse_matrix(data: dict) -> KnowledgeMatrix:
    sectors: list[SectorEntry] = []
    for row in data.get("sectors", []):
        products = tuple(
            ProductMapping(
                slug=str(p.get("slug", "")),
                name=str(p.get("name", "")),
                needs=tuple(p.get("needs") or []),
                cta=str(p.get("cta") or "DIAGNÓSTICO"),
                landing_path=str(p.get("landing_path") or "https://n8n.etsrv.site/guia/"),
            )
            for p in row.get("products") or []
        )
        sectors.append(
            SectorEntry(
                sector_id=str(row.get("sector_id", "")),
                label=str(row.get("label", "")),
                keywords=tuple(row.get("keywords") or []),
                products=products,
            )
        )
    brand_defaults = {
        str(brand): BrandDefault(
            sector_id=str(meta.get("sector_id", "")),
            product_slug=str(meta.get("product_slug", "")),
        )
        for brand, meta in (data.get("brand_defaults") or {}).items()
    }
    return KnowledgeMatrix(
        version=int(data.get("version") or 1),
        updated_at=str(data.get("updated_at") or ""),
        sectors=tuple(sectors),
        brand_defaults=brand_defaults,
    )


class JsonKnowledgeMatrixRepository:
    def load(self, tenant_id: str) -> KnowledgeMatrix:
        candidates = [
            BASE_DIR / "Marketing" / "tenants" / tenant_id / "knowledge" / "sectors.json",
            BASE_DIR / "Marketing" / "knowledge" / "sectors.json",
        ]
        for path in candidates:
            if path.is_file():
                return _parse_matrix(json.loads(path.read_text(encoding="utf-8")))
        return KnowledgeMatrix(version=1, updated_at="", sectors=(), brand_defaults={})
