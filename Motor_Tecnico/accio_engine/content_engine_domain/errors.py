from __future__ import annotations


class ContentEngineError(Exception):
    code = "content_error"
    http_status = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ContentNotFound(ContentEngineError):
    code = "content_not_found"
    http_status = 404


class ContentInvalidStatus(ContentEngineError):
    code = "content_invalid_status"
