"""Fixtures for 8311 ONU Monitor tests."""
from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME


@pytest.fixture
def mock_config_entry_data() -> dict:
    """Return mock config entry data."""
    return {
        CONF_HOST: "192.168.11.1",
        CONF_USERNAME: "root",
        CONF_PASSWORD: "testpass",
        CONF_PORT: 22,
    }


@pytest.fixture
def mock_was110_data() -> dict:
    """Return mock WAS-110 data."""
    return {
        "ssh_connected": True,
        "pon_link": True,
        "rx_power_dbm": -14.96,
        "rx_power_mw": 0.0319,
        "tx_power_dbm": 5.36,
        "tx_power_mw": 3.44,
        "optic_temperature": 38.5,
        "voltage": 3.46,
        "tx_bias_current": 11.0,
        "cpu0_temperature": 47.5,
        "cpu1_temperature": 46.8,
        "ethernet_speed": 10000,
        "vendor": "OEM",
        "part_number": "XGSPONST2001",
        "serial_number": "WAS110TEST123",
        "hardware_revision": "A-01",
        "pon_mode": "XGS-PON",
        "firmware_bank": "A",
        "pon_state_code": 51,
        "pon_state_name": "O5.1 - Associated state",
        "pon_time_in_state": 86400,
        "consecutive_errors": 0,
    }


@pytest.fixture
def mock_asyncssh() -> Generator[MagicMock]:
    """Mock asyncssh for connection tests."""
    with patch(
        "custom_components.was110_8311.config_flow.asyncssh"
    ) as mock_ssh:
        mock_conn = AsyncMock()
        mock_conn.run = AsyncMock()
        mock_conn.run.return_value = MagicMock(stdout="test")
        mock_conn.close = MagicMock()
        mock_conn.wait_closed = AsyncMock()

        mock_ssh.connect = AsyncMock(return_value=mock_conn)
        mock_ssh.PermissionDenied = Exception
        mock_ssh.Error = Exception

        yield mock_ssh
