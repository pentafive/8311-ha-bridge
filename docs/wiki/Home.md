# 8311 HA Bridge Wiki

Welcome to the 8311 HA Bridge wiki - documentation for monitoring your XGS-PON ONU running [8311 community firmware](https://github.com/up-n-atom/8311) with Home Assistant.

## Quick Links

- [[KPI-Reference]] - **NEW!** Understanding each metric and what to look for
- [[UCG-Fiber-Setup]] - UniFi gateway configuration
- [[Troubleshooting]] - Common issues and solutions
- [[Alternative-Deployments]] - systemd, Proxmox, Synology, etc.
- [[Dashboard-Examples]] - Home Assistant dashboard configs

## Overview

8311 HA Bridge monitors your XGS-PON ONU in Home Assistant:

**Optical Metrics:**
- RX/TX Power (dBm and mW)
- Voltage and TX Bias Current
- Optic Temperature

**System Health:**
- CPU Temperatures (CPU0, CPU1)
- Memory Usage (% and KB)
- ONU Uptime

**Network Status:**
- PON Link Status with state codes
- PON State (O5.1 Associated, etc.)
- Ethernet Speed (10Gbps)
- SSH Connection Health

**Device Info:**
- ISP Detection (AT&T, Frontier, Bell Canada, etc.)
- Vendor, Part Number, Hardware Revision
- Module Type (potron, bfw)
- PON Mode (XGS-PON)
- Active Firmware Bank

**Diagnostics (v2.0.0+):**
- GTC BIP Errors
- GTC FEC Corrected/Uncorrected
- LODS Events
- GPON Serial, PON Vendor ID

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

## Screenshots

### Dashboard

![Dashboard](https://raw.githubusercontent.com/pentafive/8311-ha-bridge/main/images/dashboard-main.png)

### Sensors

![Sensors](https://raw.githubusercontent.com/pentafive/8311-ha-bridge/main/images/sensors-list.png)

### Diagnostics

![Diagnostics](https://raw.githubusercontent.com/pentafive/8311-ha-bridge/main/images/sensors-diagnostic.png)

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
