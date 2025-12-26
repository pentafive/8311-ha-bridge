# Home Assistant Dashboard Examples

Example Lovelace configurations for displaying 8311 HA Bridge data.

## Screenshots

### Main Dashboard View

A complete dashboard showing Core Optical & System Health tiles alongside ONU Performance History graphs:

![Main Dashboard](https://raw.githubusercontent.com/pentafive/8311-ha-bridge/main/images/dashboard-main.png)

**Left Panel - Core Optical & System Health:**
- RX/TX Power (dBm), Optic Temp, Voltage, TX Bias, CPU Temp
- PON Link status, SSH Link status, Ethernet Speed
- Device info: Vendor, Part Number, PON Mode, Bridge Uptime

**Right Panel - ONU Performance History:**
- RX/TX Power over time (dBm)
- Temperature graphs (Optic + CPU)
- Voltage stability
- TX Bias current

### Sensor Entity List

All sensors created by the integration:

![Sensors List](https://raw.githubusercontent.com/pentafive/8311-ha-bridge/main/images/sensors-list.png)

### Entity Detail Views

**RX Power with History:**

![RX Power Entity](https://raw.githubusercontent.com/pentafive/8311-ha-bridge/main/images/entity-rx-power.png)

Shows 5-minute aggregated history graph with source attribute (eeprom51).

**PON Link Status:**

![PON Link Entity](https://raw.githubusercontent.com/pentafive/8311-ha-bridge/main/images/entity-pon-link.png)

Shows connection history, state code (51 = O5.1 Associated), and time in current state.

---

## Basic Card

Simple entities card showing key metrics:

```yaml
type: entities
title: Fiber ONT Status
entities:
  - entity: sensor.8311_onu_rx_power_dbm
    name: RX Power
  - entity: sensor.8311_onu_tx_power_dbm
    name: TX Power
  - entity: sensor.8311_onu_optic_temperature
    name: Temperature
  - entity: binary_sensor.8311_onu_pon_link_status
    name: PON Link
  - entity: binary_sensor.8311_onu_ssh_connection_status
    name: Bridge Status
```

## Tile Cards with Color Thresholds

Requires [card-mod](https://github.com/thomasloven/lovelace-card-mod) from HACS:

```yaml
type: grid
columns: 3
cards:
  - type: tile
    entity: sensor.8311_onu_rx_power_dbm
    name: RX Power
    icon: mdi:arrow-down-bold-hexagon-outline
    color: green
    card_mod:
      style: |
        ha-card {
          {% set val = states(config.entity) | float(-100) %}
          {% if val < -28 %} --tile-color: #db4437;
          {% elif val < -27 %} --tile-color: #ffa600;
          {% endif %}
        }
  - type: tile
    entity: sensor.8311_onu_tx_power_dbm
    name: TX Power
    icon: mdi:arrow-up-bold-hexagon-outline
    color: green
    card_mod:
      style: |
        ha-card {
          {% set val = states(config.entity) | float(0) %}
          {% if val < 2 or val > 9 %} --tile-color: #db4437;
          {% elif val < 4 or val > 7 %} --tile-color: #ffa600;
          {% endif %}
        }
  - type: tile
    entity: sensor.8311_onu_optic_temperature
    name: Optic Temp
    icon: mdi:thermometer
    color: green
    card_mod:
      style: |
        ha-card {
          {% set val = states(config.entity) | float(0) %}
          {% if val > 70 %} --tile-color: #db4437;
          {% elif val > 60 %} --tile-color: #ffa600;
          {% endif %}
        }
```

## History Graph

Track optical performance over time:

```yaml
type: history-graph
title: Fiber Optical Performance
hours_to_show: 24
entities:
  - entity: sensor.8311_onu_rx_power_dbm
    name: RX Power
  - entity: sensor.8311_onu_tx_power_dbm
    name: TX Power
```

## Full Dashboard with History Explorer

Requires [history-explorer-card](https://github.com/alexarch21/history-explorer-card) and [Mushroom](https://github.com/piitaya/lovelace-mushroom) from HACS.

See the [example dashboard](https://github.com/pentafive/8311-ha-bridge/blob/main/examples/home_assistant_dashboard.yaml) in the repo for a complete configuration.

## Useful Automations

### Alert on Connection Loss

```yaml
alias: "Alert: Fiber Bridge Offline"
trigger:
  - platform: state
    entity_id: binary_sensor.8311_onu_ssh_connection_status
    to: "off"
    for:
      minutes: 5
action:
  - service: notify.mobile_app
    data:
      title: "Fiber Monitor Offline"
      message: "8311 HA Bridge lost connection to WAS-110"
```

### Alert on Low RX Power

```yaml
alias: "Alert: Low Fiber RX Power"
trigger:
  - platform: numeric_state
    entity_id: sensor.8311_onu_rx_power_dbm
    below: -27
    for:
      minutes: 10
action:
  - service: notify.mobile_app
    data:
      title: "Fiber Signal Warning"
      message: "RX power is {{ states('sensor.8311_onu_rx_power_dbm') }} dBm"
```

## Contributing

Share your dashboard configs! Open a PR or submit an issue with your setup.
