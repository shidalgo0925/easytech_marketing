from __future__ import annotations

import re
import unicodedata

from Motor_Tecnico.accio_engine.knowledge_matrix_domain.model import (
    ClassificationResult,
    KnowledgeMatrix,
    ProductMapping,
    SectorEntry,
)
from Motor_Tecnico.accio_engine.knowledge_matrix_domain.ports import KnowledgeMatrixRepository


def _normalize(text: str) -> str:
    raw = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in raw if not unicodedata.combining(ch))


def _tokenize(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", _normalize(text)) if t}


class KnowledgeMatrixService:
    def __init__(self, repository: KnowledgeMatrixRepository) -> None:
        self._repo = repository

    def get_matrix(self, tenant_id: str) -> KnowledgeMatrix:
        return self._repo.load(tenant_id)

    def classify_text(self, tenant_id: str, text: str) -> ClassificationResult | None:
        matrix = self._repo.load(tenant_id)
        tokens = _tokenize(text)
        if not tokens:
            return None

        best_sector: SectorEntry | None = None
        best_score = 0
        matched: tuple[str, ...] = ()
        for sector in matrix.sectors:
            hits = tuple(kw for kw in sector.keywords if _normalize(kw) in tokens or _normalize(kw) in _normalize(text))
            score = len(hits)
            if score > best_score:
                best_score = score
                best_sector = sector
                matched = hits

        if best_sector is None or best_score == 0:
            return None

        product = best_sector.products[0] if best_sector.products else None
        if product is None:
            return None
        return ClassificationResult(
            sector_id=best_sector.sector_id,
            sector_label=best_sector.label,
            product_slug=product.slug,
            product_name=product.name,
            need=product.needs[0] if product.needs else "",
            cta=product.cta,
            landing_url=product.landing_path,
            confidence=min(1.0, 0.4 + best_score * 0.15),
            matched_keywords=matched,
        )

    def classify_brand(self, tenant_id: str, brand_id: str) -> ClassificationResult | None:
        matrix = self._repo.load(tenant_id)
        default = matrix.brand_defaults.get(brand_id) or matrix.brand_defaults.get("default")
        if default is None:
            return None

        sector = next((s for s in matrix.sectors if s.sector_id == default.sector_id), None)
        if sector is None:
            return None

        product = next((p for p in sector.products if p.slug == default.product_slug), None)
        if product is None and sector.products:
            product = sector.products[0]
        if product is None:
            return None

        return ClassificationResult(
            sector_id=sector.sector_id,
            sector_label=sector.label,
            product_slug=product.slug,
            product_name=product.name,
            need=product.needs[0] if product.needs else "",
            cta=product.cta,
            landing_url=product.landing_path,
            confidence=1.0,
            matched_keywords=("brand_default",),
        )

    def resolve_product(self, tenant_id: str, *, brand_id: str, text: str = "") -> ClassificationResult:
        by_brand = self.classify_brand(tenant_id, brand_id)
        if by_brand is not None:
            return by_brand
        by_text = self.classify_text(tenant_id, text)
        if by_text is not None:
            return by_text
        matrix = self._repo.load(tenant_id)
        sector = next((s for s in matrix.sectors if s.sector_id == "servicios"), None)
        product: ProductMapping | None = sector.products[0] if sector and sector.products else None
        return ClassificationResult(
            sector_id="servicios",
            sector_label="Servicios B2B",
            product_slug=product.slug if product else "default",
            product_name=product.name if product else "EasyTech",
            need=product.needs[0] if product and product.needs else "transformación digital",
            cta=product.cta if product else "DIAGNÓSTICO",
            landing_url=product.landing_path if product else "https://n8n.etsrv.site/guia/",
            confidence=0.5,
            matched_keywords=(),
        )
