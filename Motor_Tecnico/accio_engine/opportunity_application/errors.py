from __future__ import annotations


class ApplicationError(Exception):
    def __init__(self, code: str, message: str, http_status: int = 400) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)

    @classmethod
    def from_domain(cls, exc: Exception) -> "ApplicationError":
        code = getattr(exc, "code", "domain_error")
        message = getattr(exc, "message", str(exc))
        status = getattr(exc, "http_status", 400)
        return cls(code, message, status)
