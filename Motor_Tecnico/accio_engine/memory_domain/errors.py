from __future__ import annotations


class MemoryDomainError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class MemoryEventNotFound(MemoryDomainError):
    def __init__(self, event_id: str) -> None:
        super().__init__("not_found", f"Memory event not found: {event_id}")


class MemoryValidationError(MemoryDomainError):
    pass
