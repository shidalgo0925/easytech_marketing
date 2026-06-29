from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from Motor_Tecnico.accio_engine.marketing_plan_domain.errors import DomainError


class ApplicationErrorCode(str, Enum):
    FORBIDDEN = "Forbidden"
    CONTEXT_INVALID = "ContextInvalid"


@dataclass(frozen=True)
class ApplicationError(Exception):
    code: ApplicationErrorCode | str
    message: str
    source: Literal["auth", "context", "domain"]
    domain_error: DomainError | None = None

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"

    @classmethod
    def from_domain(cls, error: DomainError) -> ApplicationError:
        return cls(
            code=error.code.value,
            message=error.message,
            source="domain",
            domain_error=error,
        )

    @classmethod
    def forbidden(cls, message: str = "Permiso denegado") -> ApplicationError:
        return cls(code=ApplicationErrorCode.FORBIDDEN, message=message, source="auth")

    @classmethod
    def context_invalid(cls, message: str) -> ApplicationError:
        return cls(code=ApplicationErrorCode.CONTEXT_INVALID, message=message, source="context")
