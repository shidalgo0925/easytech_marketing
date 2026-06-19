"""Registro y estado de conectores multicanal (Fase D)."""

from Motor_Tecnico.connectors.registry import (
    connector_status,
    get_connector,
    is_configured,
    list_connectors,
    load_registry,
    platform_stats,
)

__all__ = [
    "load_registry",
    "list_connectors",
    "get_connector",
    "is_configured",
    "connector_status",
    "platform_stats",
]
