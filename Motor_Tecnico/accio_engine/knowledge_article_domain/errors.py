from __future__ import annotations


class KnowledgeArticleError(Exception):
    code = "knowledge_error"
    http_status = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class KnowledgeArticleNotFound(KnowledgeArticleError):
    code = "knowledge_not_found"
    http_status = 404
