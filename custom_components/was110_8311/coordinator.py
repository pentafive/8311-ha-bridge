"""DataUpdateCoordinator for 8311 ONU Monitor."""
from __future__ import annotations

import asyncio
import base64
import contextlib
import logging
import math
from datetime import timedelta
from typing import Any

import asyncssh
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ISP_PREFIXES,
    PON_STATES,
)

_LOGGER = logging.getLogger(__name__)


class WAS110Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage 8311 ONU data fetching."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.host = entry.data[CONF_HOST]
        self.username = entry.data.get(CONF_USERNAME, "root")
        self.password = entry.data.get(CONF_PASSWORD, "")
        self.port = entry.data.get(CONF_PORT, DEFAULT_PORT)
        self._connection: asyncssh.SSHClientConnection | None = None
        self._device_info: dict[str, Any] = {}
        self._consecutive_errors = 0

        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self._device_info

    async def _async_connect(self) -> asyncssh.SSHClientConnection:
        """Establish SSH connection to the ONU."""
        try:
            conn = await asyncssh.connect(
                self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                known_hosts=None,
                connect_timeout=10,
            )
            _LOGGER.debug("SSH connection established to %s", self.host)
            return conn
        except asyncssh.PermissionDenied as err:
            raise ConfigEntryAuthFailed(
                f"Authentication failed for {self.username}@{self.host}"
            ) from err
        except (OSError, asyncssh.Error) as err:
            raise UpdateFailed(f"Unable to connect to {self.host}: {err}") from err

    async def _async_run_command(self, command: str) -> str | None:
        """Run a command on the ONU."""
        try:
            if self._connection is None or self._connection.is_closed:
                self._connection = await self._async_connect()

            result = await asyncio.wait_for(
                self._connection.run(command, check=True),
                timeout=10,
            )
            return result.stdout.strip()
        except TimeoutError:
            _LOGGER.warning("Command timed out: %s", command)
            self._connection = None
            return None
        except asyncssh.ProcessError as err:
            _LOGGER.warning("Command failed: %s - %s", command, err)
            return None
        except (OSError, asyncssh.Error) as err:
            _LOGGER.warning("SSH error: %s", err)
            self._connection = None
            return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the ONU."""
        data: dict[str, Any] = {
            "ssh_connected": False,
            "pon_link": False,
        }

        try:
            # Combined command to minimize SSH sessions
            # Note: active_fwbank requires sourcing /lib/8311.sh first
            # PON mode is at gpon.ponip.pon_mode (not gpon.onu.pon_mode)
            combined_cmd = (
                "echo '---EEPROM50---' && "
                "cat /sys/class/pon_mbox/pon_mbox0/device/eeprom50 2>/dev/null | base64 && "
                "echo '---EEPROM51---' && "
                "cat /sys/class/pon_mbox/pon_mbox0/device/eeprom51 2>/dev/null | base64 && "
                "echo '---PON_STATUS---' && "
                "pon psg 2>/dev/null && "
                "echo '---CPU_TEMPS---' && "
                "cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null && "
                "echo '---ETH_SPEED---' && "
                "cat /sys/class/net/eth0_0/speed 2>/dev/null && "
                "echo '---FW_BANK---' && "
                ". /lib/8311.sh 2>/dev/null && active_fwbank 2>/dev/null || echo unknown && "
                "echo '---PON_MODE---' && "
                "uci get gpon.ponip.pon_mode 2>/dev/null || echo unknown && "
                "echo '---GPON_SERIAL---' && "
                "uci get gpon.ploam.nSerial 2>/dev/null || echo unknown && "
                "echo '---MODULE_TYPE---' && "
                ". /lib/8311.sh 2>/dev/null && get_8311_module_type 2>/dev/null || echo unknown && "
                "echo '---VENDOR_ID---' && "
                ". /lib/8311.sh 2>/dev/null && get_8311_vendor_id 2>/dev/null || echo unknown && "
                "echo '---SYSTEM_INFO---' && "
                "cat /proc/uptime 2>/dev/null && free 2>/dev/null | grep Mem && "
                "echo '---GTC_COUNTERS---' && "
                "pon gtc_counters_get 2>/dev/null && "
                "echo '---END---'"
            )

            output = await self._async_run_command(combined_cmd)
            if output is None:
                self._consecutive_errors += 1
                raise UpdateFailed(
                    f"Failed to communicate with ONU at {self.host}"
                )

            data["ssh_connected"] = True
            self._consecutive_errors = 0

            # Parse the combined output
            sections = self._parse_sections(output)

            # Parse EEPROM50 (device info)
            if "EEPROM50" in sections:
                eeprom50_data = self._decode_eeprom(sections["EEPROM50"])
                if eeprom50_data:
                    device_info = self._parse_eeprom50(eeprom50_data)
                    data.update(device_info)
                    self._device_info = device_info

            # Parse EEPROM51 (optical diagnostics)
            if "EEPROM51" in sections:
                eeprom51_data = self._decode_eeprom(sections["EEPROM51"])
                if eeprom51_data:
                    optical_data = self._parse_eeprom51(eeprom51_data)
                    data.update(optical_data)

            # Parse PON status
            if "PON_STATUS" in sections:
                pon_data = self._parse_pon_status(sections["PON_STATUS"])
                data.update(pon_data)

            # Parse CPU temperatures
            if "CPU_TEMPS" in sections:
                cpu_temps = self._parse_cpu_temps(sections["CPU_TEMPS"])
                data.update(cpu_temps)

            # Parse Ethernet speed
            if "ETH_SPEED" in sections:
                with contextlib.suppress(ValueError):
                    data["ethernet_speed"] = int(sections["ETH_SPEED"])

            # Parse firmware bank
            if "FW_BANK" in sections:
                fw_bank = sections["FW_BANK"].strip()
                if fw_bank and fw_bank.lower() != "unknown":
                    data["firmware_bank"] = fw_bank

            # Parse PON mode
            if "PON_MODE" in sections:
                pon_mode = sections["PON_MODE"].strip().upper()
                if pon_mode and pon_mode != "UNKNOWN":
                    # Format PON mode (e.g., "XGSPON" -> "XGS-PON")
                    if "PON" in pon_mode and "-PON" not in pon_mode:
                        pon_mode = pon_mode.replace("PON", "-PON")
                    data["pon_mode"] = pon_mode

            # Parse GPON serial and detect ISP
            if "GPON_SERIAL" in sections:
                gpon_serial = sections["GPON_SERIAL"].strip()
                if gpon_serial and gpon_serial.lower() != "unknown":
                    data["gpon_serial"] = gpon_serial
                    # Detect ISP from serial prefix (first 4 chars)
                    prefix = gpon_serial[:4].upper()
                    data["isp"] = ISP_PREFIXES.get(prefix, "Unknown")

            # Parse module type
            if "MODULE_TYPE" in sections:
                module_type = sections["MODULE_TYPE"].strip()
                if module_type and module_type.lower() != "unknown":
                    data["module_type"] = module_type

            # Parse vendor ID
            if "VENDOR_ID" in sections:
                vendor_id = sections["VENDOR_ID"].strip()
                if vendor_id and vendor_id.lower() != "unknown":
                    data["pon_vendor_id"] = vendor_id

            # Parse system info (uptime and memory)
            if "SYSTEM_INFO" in sections:
                sys_info = self._parse_system_info(sections["SYSTEM_INFO"])
                data.update(sys_info)

            # Parse GTC counters
            if "GTC_COUNTERS" in sections:
                gtc_data = self._parse_gtc_counters(sections["GTC_COUNTERS"])
                data.update(gtc_data)

            data["consecutive_errors"] = self._consecutive_errors
            return data

        except ConfigEntryAuthFailed:
            raise
        except UpdateFailed:
            raise
        except Exception as err:
            self._consecutive_errors += 1
            raise UpdateFailed(f"Error fetching ONU data: {err}") from err

    def _parse_sections(self, output: str) -> dict[str, str]:
        """Parse the combined command output into sections."""
        sections: dict[str, str] = {}
        current_section = None
        current_content: list[str] = []

        for line in output.split("\n"):
            if line.startswith("---") and line.endswith("---"):
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content)
                section_name = line.strip("-")
                if section_name != "END":
                    current_section = section_name
                    current_content = []
                else:
                    current_section = None
            elif current_section:
                current_content.append(line)

        if current_section and current_content:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _decode_eeprom(self, base64_data: str) -> bytes | None:
        """Decode base64 EEPROM data."""
        try:
            return base64.b64decode(base64_data.strip())
        except Exception:
            return None

    def _parse_eeprom50(self, raw_bytes: bytes) -> dict[str, Any]:
        """Parse EEPROM50 for device information."""
        data: dict[str, Any] = {}

        if len(raw_bytes) < 96:
            return data

        try:
            # Vendor Name (bytes 20-35)
            data["vendor"] = raw_bytes[20:36].decode("ascii", errors="ignore").strip()

            # Part Number (bytes 40-55)
            data["part_number"] = (
                raw_bytes[40:56].decode("ascii", errors="ignore").strip()
            )

            # Serial Number (bytes 68-83)
            data["serial_number"] = (
                raw_bytes[68:84].decode("ascii", errors="ignore").strip()
            )

            # Hardware Revision (bytes 56-59)
            data["hardware_revision"] = (
                raw_bytes[56:60].decode("ascii", errors="ignore").strip()
            )

        except Exception as err:
            _LOGGER.debug("Error parsing EEPROM50: %s", err)

        return data

    def _parse_eeprom51(self, raw_bytes: bytes) -> dict[str, Any]:
        """Parse EEPROM51 for real-time optical diagnostics."""
        data: dict[str, Any] = {}

        if len(raw_bytes) < 106:
            return data

        try:
            # Optic Temperature (Bytes 96-97)
            data["optic_temperature"] = round(
                raw_bytes[96] + (raw_bytes[97] / 256.0), 2
            )

            # Voltage (Bytes 98-99)
            data["voltage"] = round(
                ((raw_bytes[98] << 8) + raw_bytes[99]) / 10000.0, 3
            )

            # TX Bias (Bytes 100-101)
            data["tx_bias_current"] = round(
                ((raw_bytes[100] << 8) + raw_bytes[101]) / 500.0, 2
            )

            # TX Power (Bytes 102-103)
            tx_power_raw = (raw_bytes[102] << 8) + raw_bytes[103]
            tx_power_mw = tx_power_raw / 10000.0
            data["tx_power_mw"] = round(tx_power_mw, 4)
            data["tx_power_dbm"] = self._watts_to_dbm(tx_power_mw)

            # RX Power (Bytes 104-105)
            rx_power_raw = (raw_bytes[104] << 8) + raw_bytes[105]
            rx_power_mw = rx_power_raw / 10000.0
            data["rx_power_mw"] = round(rx_power_mw, 4)
            data["rx_power_dbm"] = self._watts_to_dbm(rx_power_mw)

        except Exception as err:
            _LOGGER.debug("Error parsing EEPROM51: %s", err)

        return data

    def _parse_pon_status(self, output: str) -> dict[str, Any]:
        """Parse PON status output.

        Output format: errorcode=0 current=51 previous=40 time_curr=297761
        """
        data: dict[str, Any] = {}

        # Parse space-separated key=value pairs
        for part in output.split():
            if "=" in part:
                key, value = part.split("=", 1)
                key = key.strip()
                value = value.strip()

                if key == "current":
                    with contextlib.suppress(ValueError):
                        state_code = int(value)
                        data["pon_state_code"] = state_code
                        data["pon_state_name"] = PON_STATES.get(
                            state_code, f"Unknown ({state_code})"
                        )
                        # O5.x states are operational
                        data["pon_link"] = state_code in [50, 51, 52]
                elif key == "previous":
                    with contextlib.suppress(ValueError):
                        prev_code = int(value)
                        data["pon_previous_state"] = PON_STATES.get(
                            prev_code, f"Unknown ({prev_code})"
                        )
                elif key == "time_curr":
                    with contextlib.suppress(ValueError):
                        data["pon_time_in_state"] = int(value)

        return data

    def _parse_system_info(self, output: str) -> dict[str, Any]:
        """Parse system uptime and memory info."""
        data: dict[str, Any] = {}
        lines = output.strip().split("\n")

        # First line is uptime: "299633.80 285601.51"
        if lines:
            uptime_parts = lines[0].split()
            if uptime_parts:
                with contextlib.suppress(ValueError):
                    data["onu_uptime"] = int(float(uptime_parts[0]))

        # Second line is memory: "Mem: total used free shared buff/cache available"
        if len(lines) > 1:
            mem_parts = lines[1].split()
            if len(mem_parts) >= 4:
                with contextlib.suppress(ValueError):
                    data["memory_total"] = int(mem_parts[1])
                    data["memory_used"] = int(mem_parts[2])
                    data["memory_free"] = int(mem_parts[3])
                    if data["memory_total"] > 0:
                        data["memory_percent"] = round(
                            (data["memory_used"] / data["memory_total"]) * 100, 1
                        )

        return data

    def _parse_gtc_counters(self, output: str) -> dict[str, Any]:
        """Parse GTC frame counters.

        Output format: errorcode=0 bip_errors=0 disc_gem_frames=... fec_codewords_corr=0 ...
        """
        data: dict[str, Any] = {}

        for part in output.split():
            if "=" in part:
                key, value = part.split("=", 1)

                with contextlib.suppress(ValueError):
                    if key == "bip_errors":
                        data["gtc_bip_errors"] = int(value)
                    elif key == "fec_codewords_corr":
                        data["gtc_fec_corrected"] = int(value)
                    elif key == "fec_codewords_uncorr":
                        data["gtc_fec_uncorrected"] = int(value)
                    elif key == "lods_events":
                        data["gtc_lods_events"] = int(value)

        return data

    def _parse_cpu_temps(self, output: str) -> dict[str, Any]:
        """Parse CPU temperature readings."""
        data: dict[str, Any] = {}
        temps = []

        for line in output.split("\n"):
            line = line.strip()
            if line.isdigit():
                # Convert millidegrees to degrees
                temps.append(int(line) / 1000.0)

        if len(temps) >= 1:
            data["cpu0_temperature"] = round(temps[0], 1)
        if len(temps) >= 2:
            data["cpu1_temperature"] = round(temps[1], 1)

        return data

    @staticmethod
    def _watts_to_dbm(mw: float) -> float:
        """Convert milliwatts to dBm."""
        if mw <= 0:
            return -100.0
        return round(10 * math.log10(mw), 2)

    async def async_close(self) -> None:
        """Close the SSH connection."""
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            await self._connection.wait_closed()
            self._connection = None
