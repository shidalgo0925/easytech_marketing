from __future__ import annotations


class PublicationError(Exception):
    code = "publication_error"
    http_status = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class PublicationNotFound(PublicationError):
    code = "publication_not_found"
    http_status = 404
