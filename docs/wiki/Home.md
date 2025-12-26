# 8311 HA Bridge Wiki

Welcome to the 8311 HA Bridge wiki - documentation for monitoring your XGS-PON ONU running [8311 community firmware](https://github.com/up-n-atom/8311) with Home Assistant.

## Quick Links

- [[UCG-Fiber-Setup]] - UniFi gateway configuration
- [[Troubleshooting]] - Common issues and solutions
- [[Alternative-Deployments]] - systemd, Proxmox, Synology, etc.
- [[Dashboard-Examples]] - Home Assistant dashboard configs

## Overview

8311 HA Bridge monitors your XGS-PON ONU in Home Assistant:

- **Optical Power** - RX/TX levels in dBm and mW
- **Temperature** - Optic module and CPU temps
- **Voltage & Current** - VCC and laser bias
- **Link Status** - PON state with detailed codes
- **Device Info** - Firmware, serial, hardware revision

## Supported Hardware

Works with any ONU running **8311 community firmware**:
- BFW Solutions WAS-110
- Potron Technology GP7001X
- Other [8311-compatible devices](https://github.com/up-n-atom/8311)

## Installation Options

### Option 1: HACS Integration (Recommended)

Native Home Assistant integration with UI configuration:

1. Open HACS → Custom repositories
2. Add `https://github.com/pentafive/8311-ha-bridge` as Integration
3. Install "8311 ONU Monitor"
4. Restart Home Assistant
5. Add integration via Settings → Devices & Services

### Option 2: Docker/MQTT Bridge

Container deployment with MQTT auto-discovery:

1. Clone repo and configure `.env`
2. Run `docker-compose up -d`
3. Sensors auto-discover in Home Assistant

See [README](https://github.com/pentafive/8311-ha-bridge#readme) for detailed instructions.

## Getting Started

1. Install [8311 community firmware](https://github.com/up-n-atom/8311) on your ONU
2. Configure network routing (see [[UCG-Fiber-Setup]] for UniFi)
3. Choose HACS or Docker deployment
4. Sensors appear automatically in Home Assistant

## Contributing

Found a solution? Add it to the wiki! Common contributions:

- Router/gateway setup guides
- Dashboard configurations
- Troubleshooting tips
- Alternative deployment methods
