from __future__ import annotations


class BrandError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class BrandNotFound(BrandError):
    def __init__(self, tenant_id: str, brand_id: str) -> None:
        super().__init__("not_found", f"Brand not found: {tenant_id}/{brand_id}")
