from __future__ import annotations


class CompanyBrainError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class CompanyBrainNotFound(CompanyBrainError):
    def __init__(self, tenant_id: str) -> None:
        super().__init__("not_found", f"Company brain not found for tenant: {tenant_id}")
