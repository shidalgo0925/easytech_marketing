from __future__ import annotations


class LeadError(Exception):
    code = "lead_error"
    http_status = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class LeadNotFound(LeadError):
    code = "lead_not_found"
    http_status = 404
