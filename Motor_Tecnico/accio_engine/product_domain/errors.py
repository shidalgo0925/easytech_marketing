from __future__ import annotations


class ProductError(Exception):
    code = "product_error"
    http_status = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ProductNotFound(ProductError):
    code = "product_not_found"
    http_status = 404
