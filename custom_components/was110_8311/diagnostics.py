"""Diagnostics support for 8311 ONU Monitor."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .coordinator import WAS110Coordinator

# Sensitive data to redact from diagnostics
# gpon_serial is the spoofed ISP serial - highly sensitive for authentication
TO_REDACT = {CONF_PASSWORD, "serial_number", "gpon_serial"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: WAS110Coordinator = entry.runtime_data

    return {
        "entry": {
            "data": async_redact_data(entry.data, TO_REDACT),
            "options": dict(entry.options),
        },
        "coordinator": {
            "host": coordinator.host,
            "port": coordinator.port,
            "username": coordinator.username,
            "update_interval": coordinator.update_interval.total_seconds()
            if coordinator.update_interval
            else None,
            "last_update_success": coordinator.last_update_success,
        },
        "data": async_redact_data(coordinator.data or {}, TO_REDACT),
        "device_info": async_redact_data(coordinator.device_info, TO_REDACT),
    }
