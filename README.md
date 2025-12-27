<p align="center">
  <img src="https://raw.githubusercontent.com/pentafive/8311-ha-bridge/main/images/logo.png" alt="8311 HA Bridge">
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://github.com/pentafive/8311-ha-bridge/releases"><img src="https://img.shields.io/github/v/release/pentafive/8311-ha-bridge" alt="GitHub Release"></a>
  <a href="https://github.com/pentafive/8311-ha-bridge/blob/main/LICENSE"><img src="https://img.shields.io/github/license/pentafive/8311-ha-bridge" alt="License"></a>
</p>

Monitor your XGS-PON fiber ONU running [8311 community firmware](https://github.com/up-n-atom/8311) directly in Home Assistant. Track optical power levels, temperatures, link status, and more.

## Features

- **Real-time Fiber Monitoring** - RX/TX optical power, voltage, laser bias current
- **Temperature Tracking** - Optic module and CPU temperatures
- **Link Status** - PON state with detailed status codes
- **Device Information** - Vendor, part number, firmware bank, PON mode
- **Two Deployment Options** - Native HACS integration or Docker/MQTT bridge

## Supported Hardware

This integration works with any XGS-PON ONU running **8311 community firmware**, including:
- BFW Solutions WAS-110
- Potron Technology GP7001X
- Other devices supported by [8311 firmware](https://github.com/up-n-atom/8311)

## Installation

### Option 1: HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/pentafive/8311-ha-bridge` as an **Integration**
4. Search for "8311 ONU Monitor" and install
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration**
7. Search for "8311 ONU Monitor" and configure

### Option 2: Docker/MQTT Bridge

For users who prefer container deployment or need MQTT-based integration:

1. **Clone the repository:**
    ```bash
    git clone https://github.com/pentafive/8311-ha-bridge.git
    cd 8311-ha-bridge
    ```

2. **Configure:** Copy `.env.example` to `.env` and edit:
    ```bash
    cp .env.example .env
    nano .env
    ```

3. **Run with Docker Compose:**
    ```bash
    docker-compose up -d --build
    ```

See [Alternative Deployments](https://github.com/pentafive/8311-ha-bridge/wiki/Alternative-Deployments) for systemd, Proxmox LXC, Synology, and Kubernetes options.

## Sensors

![Sensors List](https://raw.githubusercontent.com/pentafive/8311-ha-bridge/main/images/sensors-list.png)
![Diagnostic Sensors](https://raw.githubusercontent.com/pentafive/8311-ha-bridge/main/images/sensors-diagnostic.png)

| Category | Sensors |
|----------|---------|
| **Optical** | RX Power (dBm/mW), TX Power (dBm/mW), Voltage, TX Bias Current |
| **Temperature** | Optic Temperature, CPU0 Temperature, CPU1 Temperature |
| **Network** | PON Link Status, SSH Connection, Ethernet Speed, PON State |
| **Device Info** | Vendor, Part Number, Hardware Revision, PON Mode, Firmware Bank, ISP, Module Type |
| **System** | ONU Uptime, Memory Usage, Memory Used |
| **Diagnostics** | GPON Serial, PON Vendor ID, GTC BIP Errors, GTC FEC Corrected/Uncorrected, LODS Events |

## Configuration

### HACS Integration

Configure via the UI - no YAML required:
- **Host** - IP address of your ONU (usually `192.168.11.1`)
- **Username** - SSH username (usually `root`)
- **Password** - SSH password (if required)
- **Port** - SSH port (usually `22`)
- **Scan Interval** - Update frequency (10-300 seconds)

### Docker Bridge

All configuration via environment variables. See `.env.example` for the full list.

| Variable | Description | Default |
|----------|-------------|---------|
| `WAS_110_HOST` | ONU IP address | `192.168.11.1` |
| `WAS_110_PASS` | SSH password | `""` |
| `HA_MQTT_BROKER` | MQTT broker host | `homeassistant.local` |
| `HA_MQTT_PASS` | MQTT password | *required* |

## Documentation

📚 **[Full Documentation Wiki](https://github.com/pentafive/8311-ha-bridge/wiki)**

- [Home](https://github.com/pentafive/8311-ha-bridge/wiki/Home) - Overview and quick start
- [UCG-Fiber Setup](https://github.com/pentafive/8311-ha-bridge/wiki/UCG-Fiber-Setup) - UniFi gateway configuration
- [Dashboard Examples](https://github.com/pentafive/8311-ha-bridge/wiki/Dashboard-Examples) - Lovelace configs with screenshots
- [Troubleshooting](https://github.com/pentafive/8311-ha-bridge/wiki/Troubleshooting) - Common issues and solutions
- [Alternative Deployments](https://github.com/pentafive/8311-ha-bridge/wiki/Alternative-Deployments) - systemd, Proxmox, Synology, k8s

## Requirements

- **ONU Device** - Any XGS-PON ONU with [8311 community firmware](https://github.com/up-n-atom/8311)
- **SSH Access** - SSH enabled on the ONU (default: `root@192.168.11.1`)
- **Home Assistant** - 2024.1.0 or newer (for HACS integration)

### For Docker Bridge Only
- **MQTT Broker** - Mosquitto or compatible broker
- **MQTT Integration** - Home Assistant MQTT integration with discovery enabled

## Technical Details

### Data Sources

The integration reads from multiple sources on the ONU:

1. **EEPROM51** - Real-time optical diagnostics (power, temperature, voltage)
2. **EEPROM50** - Static device information (vendor, serial, part number)
3. **sysfs** - CPU temperatures, ethernet speed
4. **8311 shell** - PON status, firmware bank, GTC counters
5. **UCI config** - PON mode, GPON serial, vendor ID
6. **/proc** - System uptime, memory usage

## Version History

See [CHANGELOG.md](CHANGELOG.md) for full release history.

| Version | Type | Description |
|---------|------|-------------|
| 2.0.0 | HACS | Native Home Assistant integration |
| 1.0.x | Docker | MQTT bridge for container deployment |

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Acknowledgements

- **[8311 Community](https://github.com/up-n-atom/8311)** - Firmware and documentation
- **[PON Wiki](https://pon.wiki/)** - Comprehensive XGS-PON resources
- **[Home Assistant](https://www.home-assistant.io/)** - Home automation platform
- **[@Felaros](https://github.com/Felaros)** - Docker improvements in v1.0.2

## Resources

- [8311 Community GitHub](https://github.com/up-n-atom/8311)
- [8311 Community Discord](https://discord.pon.wiki)
- [PON Wiki - WAS-110](https://pon.wiki/xgs-pon/ont/bfw-solutions/was-110/)
- [Home Assistant MQTT Integration](https://www.home-assistant.io/integrations/mqtt/)
