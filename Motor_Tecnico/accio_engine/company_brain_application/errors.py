from __future__ import annotations


class ApplicationError(Exception):
    def __init__(self, code: str, message: str, http_status: int = 400) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)

    @classmethod
    def forbidden(cls, message: str) -> ApplicationError:
        return cls("forbidden", message, 403)

    @classmethod
    def not_found(cls, message: str) -> ApplicationError:
        return cls("not_found", message, 404)

    @classmethod
    def from_domain(cls, exc: Exception) -> ApplicationError:
        code = getattr(exc, "code", "domain_error")
        message = getattr(exc, "message", str(exc))
        if code == "not_found":
            return cls.not_found(message)
        return cls(code, message, 400)
