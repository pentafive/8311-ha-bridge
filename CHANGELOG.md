# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-03-11

### Fixed
- **SSH Connection Leak** — When SSH timeout or error occurred, the old connection was orphaned without being closed. Leaked connections accumulated on the ONU, eventually overwhelming its SSH daemon. This was the root cause of both GitHub issue #2 and the 14-hour flapping event on 2026-03-10/11. ([#2](https://github.com/pentafive/8311-ha-bridge/issues/2))

### Added
- **MQTT Last Will & Testament** (Docker bridge) — Entities go unavailable instantly when the bridge process dies, instead of waiting for MQTT keepalive timeout
- **Consecutive Errors sensor** — Real-time count of back-to-back poll failures (resets on success)
- **SSH Reconnections sensor** — Lifetime counter of SSH reconnect events
- **Error Rate sensor** — Percentage of total polls that failed
- **Total Updates sensor** — Lifetime counter of successful polls
- **Rolling Availability sensor** — Percentage of successful polls over the last 60 polling intervals (1-hour window at default interval)
- **ONU Reboot Count sensor** — Detects uptime rollback and counts reboots
- **Last Reboot Detected sensor** — Timestamp of most recent detected ONU reboot
- All new sensors are diagnostic entities — they appear under the device but don't clutter the default dashboard

### Fixed (Docker bridge)
- SSH reconnection counter was incrementing on *failed* reconnects instead of successful ones

### Changed
- `async_close()` now uses a shared `_close_connection()` helper for consistent cleanup
- SSH error paths properly close connections before reconnecting

---

## [2.0.1] - 2025-12-27

### Added
- **Home Assistant Brand Registration** - Official icon now appears in HA integrations list ([PR #8839](https://github.com/home-assistant/brands/pull/8839))

---

## [2.0.0] - 2025-12-26

### Added
- **HACS Integration** - Native Home Assistant custom component
- Config Flow UI - No more YAML configuration required
- Options Flow - Change scan interval without reconfiguring
- Re-authentication flow - Handle credential changes gracefully
- Diagnostics platform - Export device info for troubleshooting (with sensitive data redaction)
- Async SSH via `asyncssh` library - Non-blocking data fetching
- DataUpdateCoordinator pattern - Modern HA polling architecture
- CI/CD workflows - HACS validation, Hassfest, Ruff linting
- Unit tests framework with pytest
- **New Sensors:**
  - ISP detection from GPON serial prefix (AT&T, Frontier, Bell Canada, etc.)
  - GPON Serial (disabled by default for privacy)
  - Module Type (potron, bfw, etc.)
  - PON Vendor ID
  - ONU Uptime with human-readable formatting
  - Memory Usage (percentage and KB)
  - PON State name and time in state
  - GTC counters: BIP Errors, FEC Corrected/Uncorrected, LODS Events

### Fixed
- PON Link status showing "Disconnected" when connected (was parsing `state=` but actual output is `current=`)

### Changed
- Integration now installs via HACS or manual `custom_components/` copy
- Uses `asyncssh` instead of subprocess SSH for async compatibility
- Entity naming follows HA 2024 conventions (`has_entity_name = True`)
- Unique IDs based on device serial number (immutable)

### Migration
The Docker/MQTT bridge (`8311-ha-bridge.py`) remains available for users who prefer that deployment method. The HACS integration is a new alternative that runs natively in Home Assistant.

### Technical
- Target: Home Assistant 2024.1.0+
- Python 3.12+
- Follows HA Quality Scale Silver/Gold patterns

## [1.0.2] - 2025-12-25

### Added
- `PING_ENABLED` environment variable to control ping checks (default: disabled for container compatibility)
- `MQTT_CLIENT_ID` environment variable for custom MQTT client identification
- `HA_DISCOVERY_PREFIX` and `HA_ENTITY_BASE` as configurable environment variables
- `RECONNECT_DELAY_1-4` environment variables for custom backoff timing
- `iputils-ping` added to Docker image for optional connectivity checks

### Changed
- All configuration now loaded from environment variables (no more hardcoded defaults)
- `DEBUG_MODE` defaults to `False` for production use
- docker-compose.yaml now uses pure environment variable substitution (no inline fallbacks)
- Ping check now gated behind `PING_ENABLED` flag for container-friendly operation

### Thanks
- @Felaros for the fork improvements that inspired these changes

## [1.0.1] - 2025-12-25

### Fixed
- SSH connection status binary sensor showing "unknown" in Home Assistant
- Root cause: State was published before MQTT discovery config, causing Home Assistant to miss initial state
- Solution: Re-publish SSH status after discovery configs are sent, and periodically in monitoring loop

### Changed
- SSH status now includes `source` attribute ("post_discovery_sync" or "monitoring_loop")
- SSH status published on each successful metrics collection for real-time health indication

## [1.0.0] - 2025-12-03

### Added
- Initial public release
- SSH-based monitoring of WAS-110 XGS-PON ONU
- MQTT Auto Discovery for Home Assistant integration
- Real-time optical metrics (RX/TX power in dBm and mW)
- Temperature monitoring (optic module, CPU zones)
- Voltage and laser bias current monitoring
- PON link status with detailed state codes
- Ethernet speed detection
- Device information sensors (vendor, part number, firmware bank)
- Bridge uptime and statistics tracking
- Test mode for validation
- Debug mode for verbose logging
- Dockerfile for containerized deployment
- Docker Compose configuration
- Example Home Assistant dashboard configuration

### Technical
- Uses native SSH via subprocess (not paramiko) for Dropbear compatibility
- Combined SSH commands to avoid device rate limiting
- Binary EEPROM parsing (base64 encoded over SSH)
- Ping-before-SSH connectivity check
- Automatic MQTT reconnection handling

## [Unreleased]

### Planned
- PON state change counter + bridge health enum sensor
- Web UI scraping for additional metrics
