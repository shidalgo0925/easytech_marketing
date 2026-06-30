from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.knowledge_matrix_domain.model import KnowledgeMatrix


class KnowledgeMatrixRepository(Protocol):
    def load(self, tenant_id: str) -> KnowledgeMatrix: ...
