# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- HACS integration packaging
- Optional SSH connection multiplexing (ControlMaster)
