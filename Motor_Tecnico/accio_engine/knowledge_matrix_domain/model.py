from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProductMapping:
    slug: str
    name: str
    needs: tuple[str, ...] = ()
    cta: str = "DIAGNÓSTICO"
    landing_path: str = "https://n8n.etsrv.site/guia/"

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "name": self.name,
            "needs": list(self.needs),
            "cta": self.cta,
            "landing_path": self.landing_path,
        }


@dataclass(frozen=True)
class SectorEntry:
    sector_id: str
    label: str
    keywords: tuple[str, ...] = ()
    products: tuple[ProductMapping, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "sector_id": self.sector_id,
            "label": self.label,
            "keywords": list(self.keywords),
            "products": [p.to_dict() for p in self.products],
        }


@dataclass(frozen=True)
class BrandDefault:
    sector_id: str
    product_slug: str


@dataclass(frozen=True)
class KnowledgeMatrix:
    version: int
    updated_at: str
    sectors: tuple[SectorEntry, ...]
    brand_defaults: dict[str, BrandDefault]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "updated_at": self.updated_at,
            "sectors": [s.to_dict() for s in self.sectors],
            "brand_defaults": {
                brand: {"sector_id": row.sector_id, "product_slug": row.product_slug}
                for brand, row in self.brand_defaults.items()
            },
        }


@dataclass(frozen=True)
class ClassificationResult:
    sector_id: str
    sector_label: str
    product_slug: str
    product_name: str
    need: str
    cta: str
    landing_url: str
    confidence: float
    matched_keywords: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sector_id": self.sector_id,
            "sector_label": self.sector_label,
            "product_slug": self.product_slug,
            "product_name": self.product_name,
            "need": self.need,
            "cta": self.cta,
            "landing_url": self.landing_url,
            "confidence": self.confidence,
            "matched_keywords": list(self.matched_keywords),
        }
