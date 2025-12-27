# Home Assistant Dashboard Examples

Example Lovelace configurations for displaying 8311 HA Bridge data.

## Screenshots

### Sensors List

All sensors created by the integration, organized into Sensors and Diagnostic categories:

![Sensors List](https://raw.githubusercontent.com/pentafive/8311-ha-bridge/main/images/sensors-list.png)

### Diagnostic Sensors

Diagnostic sensors include device identification and GTC error counters:

![Diagnostic Sensors](https://raw.githubusercontent.com/pentafive/8311-ha-bridge/main/images/sensors-diagnostic.png)

---

## Entity ID Format

Entity IDs vary based on deployment method:

| Deployment | Example Entity ID |
|------------|-------------------|
| Docker/MQTT | `sensor.8311_onu_was110_xgspon_rx_power` |
| HACS | `sensor.8311_onu_<serial>_rx_power` |

Update the entity IDs in examples below to match your setup.

---

## Basic Card

Simple entities card showing key metrics:

```yaml
type: entities
title: Fiber ONT Status
entities:
  - entity: sensor.8311_onu_was110_xgspon_rx_power
    name: RX Power
  - entity: sensor.8311_onu_was110_xgspon_tx_power
    name: TX Power
  - entity: sensor.8311_onu_was110_xgspon_optic_temperature
    name: Temperature
  - entity: sensor.8311_onu_was110_xgspon_isp
    name: ISP
  - entity: binary_sensor.8311_onu_was110_xgspon_pon_link
    name: PON Link
```

## Device Info Card

Show ISP, module type, and uptime:

```yaml
type: entities
title: ONU Device Info
entities:
  - entity: sensor.8311_onu_was110_xgspon_isp
    name: ISP
  - entity: sensor.8311_onu_was110_xgspon_vendor
    name: Vendor
  - entity: sensor.8311_onu_was110_xgspon_module_type
    name: Module Type
  - entity: sensor.8311_onu_was110_xgspon_onu_uptime
    name: ONU Uptime
  - entity: sensor.8311_onu_was110_xgspon_memory_usage
    name: Memory Usage
  - entity: sensor.8311_onu_was110_xgspon_pon_state
    name: PON State
```

## Tile Cards with Color Thresholds

Requires [card-mod](https://github.com/thomasloven/lovelace-card-mod) from HACS:

```yaml
type: grid
columns: 3
cards:
  - type: tile
    entity: sensor.8311_onu_was110_xgspon_rx_power
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
    entity: sensor.8311_onu_was110_xgspon_tx_power
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
    entity: sensor.8311_onu_was110_xgspon_optic_temperature
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

## GTC Diagnostics Card

Monitor fiber error counters:

```yaml
type: entities
title: GTC Diagnostics
entities:
  - entity: sensor.8311_onu_was110_xgspon_gtc_bip_errors
    name: BIP Errors
  - entity: sensor.8311_onu_was110_xgspon_gtc_fec_corrected
    name: FEC Corrected
  - entity: sensor.8311_onu_was110_xgspon_gtc_fec_uncorrected
    name: FEC Uncorrected
  - entity: sensor.8311_onu_was110_xgspon_lods_events
    name: LODS Events
```

## History Graph

Track optical performance over time:

```yaml
type: history-graph
title: Fiber Optical Performance
hours_to_show: 24
entities:
  - entity: sensor.8311_onu_was110_xgspon_rx_power
    name: RX Power
  - entity: sensor.8311_onu_was110_xgspon_tx_power
    name: TX Power
```

## Full Dashboard

Requires [history-explorer-card](https://github.com/alexarch21/history-explorer-card) and [Mushroom](https://github.com/piitaya/lovelace-mushroom) from HACS.

**Choose based on your deployment:**
- [HACS Dashboard](https://github.com/pentafive/8311-ha-bridge/blob/main/examples/home_assistant_dashboard_hacs.yaml) - For HACS integration users
- [Docker Dashboard](https://github.com/pentafive/8311-ha-bridge/blob/main/examples/home_assistant_dashboard_docker.yaml) - For Docker/MQTT bridge users

The main difference is entity ID format:
- HACS: `sensor.8311_onu_<serial>_rx_power`
- Docker: `sensor.8311_onu_was110_xgspon_rx_power`

---

## Useful Automations

### Alert on Connection Loss

```yaml
alias: "Alert: Fiber Bridge Offline"
trigger:
  - platform: state
    entity_id: binary_sensor.8311_onu_was110_xgspon_pon_link
    to: "off"
    for:
      minutes: 5
action:
  - service: notify.mobile_app
    data:
      title: "Fiber Connection Lost"
      message: "PON link is down on 8311 ONU"
```

### Alert on Low RX Power

```yaml
alias: "Alert: Low Fiber RX Power"
trigger:
  - platform: numeric_state
    entity_id: sensor.8311_onu_was110_xgspon_rx_power
    below: -27
    for:
      minutes: 10
action:
  - service: notify.mobile_app
    data:
      title: "Fiber Signal Warning"
      message: "RX power is {{ states('sensor.8311_onu_was110_xgspon_rx_power') }} dBm"
```

### Alert on FEC Errors Increasing

```yaml
alias: "Alert: Fiber FEC Errors"
trigger:
  - platform: state
    entity_id: sensor.8311_onu_was110_xgspon_gtc_fec_uncorrected
action:
  - condition: template
    value_template: >
      {{ trigger.to_state.state | int(0) > trigger.from_state.state | int(0) }}
  - service: notify.mobile_app
    data:
      title: "Fiber Quality Warning"
      message: "Uncorrectable FEC errors increased to {{ states('sensor.8311_onu_was110_xgspon_gtc_fec_uncorrected') }}"
```

---

## Contributing

Share your dashboard configs! Open a PR or submit an issue with your setup.
