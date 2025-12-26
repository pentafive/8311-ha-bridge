"""Constants for the 8311 ONU Monitor integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "was110_8311"
MANUFACTURER: Final = "8311 Community"
MODEL: Final = "XGS-PON ONU"

# Configuration
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Defaults
DEFAULT_PORT: Final = 22
DEFAULT_USERNAME: Final = "root"
DEFAULT_SCAN_INTERVAL: Final = 60

# Attributes
ATTR_STATE_CODE: Final = "state_code"
ATTR_STATE_NAME: Final = "state_name"
ATTR_TIME_IN_STATE: Final = "time_in_state_seconds"
ATTR_TIME_IN_STATE_FORMATTED: Final = "time_in_state_formatted"
ATTR_CONSECUTIVE_ERRORS: Final = "consecutive_errors"

# ISP detection from GPON serial prefix
# Reference: https://pon.wiki and https://hack-gpon.org/vendor/
ISP_PREFIXES: Final = {
    # AT&T devices
    "HUMA": "AT&T",  # Humax BGW320-500
    "NOKA": "AT&T",  # Nokia BGW320-505
    "COMM": "AT&T",  # CommScope BGW620-700
    # Frontier devices
    "FTRO": "Frontier",  # FOX222, FRX523
    # Bell Canada
    "ALCL": "Bell Canada",  # Nokia/Alcatel-Lucent
    "SMBS": "Bell Canada",  # Sagemcom Giga Hub
    # Other ISPs (extend as needed)
    "HWTC": "Huawei ISP",
    "ZTEG": "ZTE ISP",
    "UBNT": "Ubiquiti",
}

# PON State mapping
PON_STATES: Final = {
    0: "O0 - Power-up state",
    10: "O1 - Initial state",
    11: "O1.1 - Off-sync state",
    12: "O1.2 - Profile learning state",
    20: "O2 - Stand-by state",
    23: "O2.3 - Serial number state",
    30: "O3 - Serial number state",
    40: "O4 - Ranging state",
    50: "O5 - Operation state",
    51: "O5.1 - Associated state",
    52: "O5.2 - Pending state",
    60: "O6 - Intermittent LOS state",
    70: "O7 - Emergency stop state",
    71: "O7.1 - Emergency stop off-sync state",
    72: "O7.2 - Emergency stop in-sync state",
    81: "O8.1 - Downstream tuning off-sync state",
    82: "O8.2 - Downstream tuning profile learning state",
    90: "O9 - Upstream tuning state",
}

