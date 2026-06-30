from __future__ import annotations

from Motor_Tecnico.accio_engine.knowledge_matrix_application.context import TenantContext
from Motor_Tecnico.accio_engine.knowledge_matrix_application.use_cases import ClassifyKnowledgeMatrix, GetKnowledgeMatrix
from Motor_Tecnico.accio_engine.knowledge_matrix_domain.service import KnowledgeMatrixService
from Motor_Tecnico.accio_engine.knowledge_matrix_infrastructure.application_adapters import KnowledgeMatrixRbacAdapter
from Motor_Tecnico.accio_engine.knowledge_matrix_infrastructure.json_repository import JsonKnowledgeMatrixRepository

_MATRIX: KnowledgeMatrixService | None = None


def get_knowledge_matrix_service() -> KnowledgeMatrixService:
    global _MATRIX
    if _MATRIX is None:
        _MATRIX = KnowledgeMatrixService(JsonKnowledgeMatrixRepository())
    return _MATRIX


def reset_knowledge_matrix_service() -> None:
    global _MATRIX
    _MATRIX = None


class KnowledgeMatrixUseCases:
    def __init__(self) -> None:
        matrix = get_knowledge_matrix_service()
        auth = KnowledgeMatrixRbacAdapter()
        self.get_matrix = GetKnowledgeMatrix(matrix, auth)
        self.classify = ClassifyKnowledgeMatrix(matrix, auth)


_USE_CASES: KnowledgeMatrixUseCases | None = None


def reset_knowledge_matrix_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None


def knowledge_matrix_use_cases() -> KnowledgeMatrixUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = KnowledgeMatrixUseCases()
    return _USE_CASES


def tenant_context(tenant_id: str) -> TenantContext:
    return TenantContext(tenant_id=tenant_id)
