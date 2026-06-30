from __future__ import annotations

from Motor_Tecnico.accio_engine.knowledge_matrix_application.context import TenantContext
from Motor_Tecnico.accio_engine.knowledge_matrix_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.knowledge_matrix_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.knowledge_matrix_domain.model import ClassificationResult, KnowledgeMatrix
from Motor_Tecnico.accio_engine.knowledge_matrix_domain.service import KnowledgeMatrixService


class GetKnowledgeMatrix:
    def __init__(self, matrix: KnowledgeMatrixService, authorization: AuthorizationPort) -> None:
        self._matrix = matrix
        self._authorization = authorization

    def __call__(self, ctx: TenantContext) -> KnowledgeMatrix:
        self._authorization.require_permission(ctx, "read")
        return self._matrix.get_matrix(ctx.tenant_id)


class ClassifyKnowledgeMatrix:
    def __init__(self, matrix: KnowledgeMatrixService, authorization: AuthorizationPort) -> None:
        self._matrix = matrix
        self._authorization = authorization

    def __call__(
        self,
        ctx: TenantContext,
        *,
        text: str = "",
        brand_id: str | None = None,
    ) -> ClassificationResult:
        self._authorization.require_permission(ctx, "read")
        if brand_id:
            result = self._matrix.resolve_product(ctx.tenant_id, brand_id=brand_id, text=text)
        elif text.strip():
            result = self._matrix.classify_text(ctx.tenant_id, text)
            if result is None:
                raise ApplicationError("no_match", "No hay sector/producto para el texto dado", 404)
            return result
        else:
            raise ApplicationError("text_or_brand_required", "Enviar text o brand_id", 400)
        return result
