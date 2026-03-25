"""Tests for the WAS110 coordinator health monitoring."""
from __future__ import annotations

from collections import deque
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.was110_8311.coordinator import WAS110Coordinator


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.data = {
        CONF_HOST: "192.168.11.1",
        CONF_USERNAME: "root",
        CONF_PASSWORD: "testpass",
        CONF_PORT: 22,
    }
    entry.options = {}
    return entry


@pytest.fixture
def coordinator(hass, mock_entry):
    """Create a coordinator instance."""
    return WAS110Coordinator(hass, mock_entry)


class TestStatsTracking:
    """Test health monitoring statistics tracking."""

    def test_initial_stats(self, coordinator):
        """Test initial stats are zero."""
        assert coordinator._total_updates == 0
        assert coordinator._total_errors == 0
        assert coordinator._consecutive_errors == 0
        assert coordinator._ssh_reconnections == 0
        assert len(coordinator._poll_results) == 0

    async def test_success_increments_updates(self, coordinator):
        """Test successful poll increments total_updates."""
        # Mock a successful SSH command with valid output
        coordinator._connection = MagicMock()
        coordinator._connection.is_closed = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.stdout = (
            "---EEPROM50---\n---EEPROM51---\n"
            "---PON_STATUS---\nerrorcode=0 current=51 previous=40 time_curr=100\n"
            "---CPU_TEMPS---\n47500\n46800\n"
            "---ETH_SPEED---\n10000\n"
            "---FW_BANK---\nA\n"
            "---PON_MODE---\nXGSPON\n"
            "---GPON_SERIAL---\nFTRO12345678\n"
            "---MODULE_TYPE---\npotron\n"
            "---VENDOR_ID---\nXGSP\n"
            "---SYSTEM_INFO---\n86400.50 80000.00\n"
            "Mem:         999424      559564      316024        2804      123836      408896\n"
            "---GTC_COUNTERS---\nerrorcode=0 bip_errors=0 fec_codewords_corr=0 fec_codewords_uncorr=0 lods_events=1\n"
            "---END---"
        )
        coordinator._connection.run = AsyncMock(return_value=mock_result)

        data = await coordinator._async_update_data()

        assert coordinator._total_updates == 1
        assert coordinator._total_errors == 0
        assert coordinator._consecutive_errors == 0
        assert data["total_updates"] == 1
        assert data["ssh_connected"] is True

    async def test_failure_increments_errors(self, coordinator):
        """Test failed poll increments error counters."""
        coordinator._connection = MagicMock()
        coordinator._connection.is_closed = MagicMock(return_value=False)
        coordinator._connection.run = AsyncMock(side_effect=TimeoutError)

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

        assert coordinator._total_errors == 1
        assert coordinator._consecutive_errors == 1

    async def test_consecutive_errors_reset_on_success(self, coordinator):
        """Test consecutive errors reset after successful poll."""
        coordinator._consecutive_errors = 5
        coordinator._total_errors = 5

        # Set up successful response
        coordinator._connection = MagicMock()
        coordinator._connection.is_closed = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.stdout = (
            "---SYSTEM_INFO---\n86400.50 80000.00\n"
            "Mem:         999424      559564      316024        2804      123836      408896\n"
            "---END---"
        )
        coordinator._connection.run = AsyncMock(return_value=mock_result)

        await coordinator._async_update_data()

        assert coordinator._consecutive_errors == 0
        assert coordinator._total_errors == 5  # Not reset


class TestRollingAvailability:
    """Test rolling availability percentage."""

    def test_empty_poll_results(self, coordinator):
        """Test availability is 100% when no polls have run."""
        assert len(coordinator._poll_results) == 0

    async def test_availability_after_successes(self, coordinator):
        """Test availability is 100% after all successes."""
        coordinator._poll_results = deque([True] * 10, maxlen=60)

        coordinator._connection = MagicMock()
        coordinator._connection.is_closed = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.stdout = "---SYSTEM_INFO---\n100.0 90.0\nMem: 999424 559564 316024 2804 123836 408896\n---END---"
        coordinator._connection.run = AsyncMock(return_value=mock_result)

        data = await coordinator._async_update_data()
        assert data["availability_pct"] == 100.0

    def test_availability_with_failures(self, coordinator):
        """Test availability calculation with mixed results."""
        coordinator._poll_results = deque(
            [True] * 50 + [False] * 10, maxlen=60
        )
        pct = round(sum(coordinator._poll_results) / len(coordinator._poll_results) * 100, 1)
        assert pct == 83.3

    def test_rolling_window_maxlen(self, coordinator):
        """Test deque maxlen limits to 60 entries."""
        for _ in range(100):
            coordinator._poll_results.append(True)
        assert len(coordinator._poll_results) == 60


class TestRebootDetection:
    """Test ONU reboot detection via uptime rollback."""

    def test_initial_state(self, coordinator):
        """Test initial reboot detection state."""
        assert coordinator._previous_uptime is None
        assert coordinator._reboot_count == 0
        assert coordinator._last_reboot_detected is None

    def test_no_false_positive_on_first_poll(self, coordinator):
        """Test first poll does not trigger reboot detection."""
        # previous_uptime is None, so any value should be fine
        assert coordinator._previous_uptime is None

    async def test_reboot_detected(self, coordinator):
        """Test reboot is detected when uptime decreases."""
        coordinator._previous_uptime = 86400  # 1 day

        coordinator._connection = MagicMock()
        coordinator._connection.is_closed = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.stdout = "---SYSTEM_INFO---\n120.0 100.0\nMem: 999424 559564 316024 2804 123836 408896\n---END---"
        coordinator._connection.run = AsyncMock(return_value=mock_result)

        data = await coordinator._async_update_data()

        assert coordinator._reboot_count == 1
        assert coordinator._last_reboot_detected is not None
        assert data["onu_reboot_count"] == 1
        assert data["last_reboot_detected"] is not None

    async def test_no_reboot_on_increasing_uptime(self, coordinator):
        """Test no reboot detected when uptime increases normally."""
        coordinator._previous_uptime = 1000

        coordinator._connection = MagicMock()
        coordinator._connection.is_closed = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.stdout = "---SYSTEM_INFO---\n1060.0 900.0\nMem: 999424 559564 316024 2804 123836 408896\n---END---"
        coordinator._connection.run = AsyncMock(return_value=mock_result)

        data = await coordinator._async_update_data()

        assert coordinator._reboot_count == 0
        assert data["onu_reboot_count"] == 0


class TestSSHConnectionLeak:
    """Test SSH connection leak fix (GitHub #2)."""

    async def test_timeout_closes_connection(self, coordinator):
        """Test that timeout properly closes the old connection."""
        mock_conn = MagicMock()
        mock_conn.is_closed = MagicMock(return_value=False)
        mock_conn.close = MagicMock()
        mock_conn.wait_closed = AsyncMock()
        mock_conn.run = AsyncMock(side_effect=TimeoutError)
        coordinator._connection = mock_conn

        result = await coordinator._async_run_command("test")

        assert result is None
        mock_conn.close.assert_called_once()
        assert coordinator._connection is None
        assert coordinator._was_disconnected is True

    async def test_ssh_error_closes_connection(self, coordinator):
        """Test that SSH error properly closes the old connection."""
        mock_conn = MagicMock()
        mock_conn.is_closed = MagicMock(return_value=False)
        mock_conn.close = MagicMock()
        mock_conn.wait_closed = AsyncMock()
        mock_conn.run = AsyncMock(side_effect=OSError("Connection reset"))
        coordinator._connection = mock_conn

        result = await coordinator._async_run_command("test")

        assert result is None
        mock_conn.close.assert_called_once()
        assert coordinator._connection is None

    async def test_reconnection_counted(self, coordinator):
        """Test SSH reconnection is counted after disconnect."""
        coordinator._was_disconnected = True
        coordinator._connection = None

        mock_conn = MagicMock()
        mock_conn.is_closed = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.stdout = "success"
        mock_conn.run = AsyncMock(return_value=mock_result)

        with patch.object(
            coordinator, "_async_connect", return_value=mock_conn
        ):
            result = await coordinator._async_run_command("echo test")

        assert result == "success"
        assert coordinator._ssh_reconnections == 1
        assert coordinator._was_disconnected is False


class TestPontopAlarms:
    """Test pontop alarm parsing (v2.2.0)."""

    def test_no_alarms(self, coordinator):
        """Test parsing when no alarms are active."""
        output = (
            "Page: Active alarms\n"
            "Alarm type       Alarm                     Description\n"
        )
        result = coordinator._parse_pontop_alarms(output)
        assert result["pon_alarms_active"] is False
        assert "pon_alarm_types" not in result

    def test_active_alarms(self, coordinator):
        """Test parsing when alarms are present."""
        output = (
            "Page: Active alarms\n"
            "Alarm type       Alarm                     Description\n"
            "LEVEL            PON_ALARM_STATIC_LOS      Loss of signal\n"
            "LEVEL            PON_ALARM_STATIC_LODS     Loss of downstream synchronization\n"
        )
        result = coordinator._parse_pontop_alarms(output)
        assert result["pon_alarms_active"] is True
        assert "PON_ALARM_STATIC_LOS" in result["pon_alarm_types"]
        assert "PON_ALARM_STATIC_LODS" in result["pon_alarm_types"]

    def test_empty_output(self, coordinator):
        """Test parsing with empty output."""
        result = coordinator._parse_pontop_alarms("")
        assert result["pon_alarms_active"] is False


class TestGEMCounters:
    """Test GEM/XGEM port counter parsing (v2.2.0)."""

    def test_parse_gem_counters(self, coordinator):
        """Test parsing real GEM counter output."""
        output = (
            "Page: GEM/XGEM Port Counters\n"
            "GEM Index       GEM ID          u/s packets     u/s bytes"
            "       d/s packets     d/s bytes       Key Errors\n"
            "0               14              462             22176"
            "           454             21792           0\n"
            "1               65534           0               0"
            "               0               0               0\n"
            "2               1068            254938585       197576881274"
            "    313027027       299502232944    0\n"
        )
        result = coordinator._parse_gem_counters(output)
        assert result["gem_downstream_bytes"] == 299502254736  # 21792 + 0 + 299502232944
        assert result["gem_upstream_bytes"] == 197576903450  # 22176 + 0 + 197576881274
        assert result["gem_key_errors"] == 0

    def test_empty_gem_output(self, coordinator):
        """Test parsing with no GEM data."""
        result = coordinator._parse_gem_counters("")
        assert result["gem_downstream_bytes"] == 0
        assert result["gem_upstream_bytes"] == 0
        assert result["gem_key_errors"] == 0

    def test_gem_key_errors(self, coordinator):
        """Test key errors are summed across ports."""
        output = (
            "Page: GEM/XGEM Port Counters\n"
            "GEM Index       GEM ID          u/s packets     u/s bytes"
            "       d/s packets     d/s bytes       Key Errors\n"
            "0               14              10              100"
            "             10              100             3\n"
            "1               1068            100             1000"
            "            100             1000            5\n"
        )
        result = coordinator._parse_gem_counters(output)
        assert result["gem_key_errors"] == 8


class TestOLTVendor:
    """Test OLT vendor parsing from OMCI ME 131 attr 1 (v2.2.0)."""

    def test_parse_olt_vendor(self, coordinator):
        """Test parsing ALCL vendor from meadg output."""
        output = "errorcode=0 attr_data=41 4c 43 4c"
        result = coordinator._parse_olt_vendor(output)
        assert result["olt_vendor"] == "ALCL"

    def test_parse_huawei_vendor(self, coordinator):
        """Test parsing HWTC vendor."""
        output = "errorcode=0 attr_data=48 57 54 43"
        result = coordinator._parse_olt_vendor(output)
        assert result["olt_vendor"] == "HWTC"

    def test_empty_output(self, coordinator):
        """Test parsing with no OMCI data."""
        result = coordinator._parse_olt_vendor("")
        assert "olt_vendor" not in result

    def test_error_output(self, coordinator):
        """Test parsing when OMCI command fails."""
        result = coordinator._parse_olt_vendor("errorcode=9")
        assert "olt_vendor" not in result


class TestCPULoad:
    """Test CPU load parsing (v2.2.0)."""

    def test_parse_loadavg(self, coordinator):
        """Test parsing /proc/loadavg output."""
        result = coordinator._parse_cpu_load("0.15 0.10 0.15 1/154 8337")
        assert result["cpu_load_1m"] == 0.15
        assert result["cpu_load_5m"] == 0.10
        assert result["cpu_load_15m"] == 0.15

    def test_empty_output(self, coordinator):
        """Test parsing with empty output."""
        result = coordinator._parse_cpu_load("")
        assert "cpu_load_1m" not in result
