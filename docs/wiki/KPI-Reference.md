# KPI Reference Guide

Understanding what each sensor means and what to look for when monitoring your XGS-PON ONU.

---

## Quick Reference: What's Normal?

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| **RX Power** | -15 to -25 dBm | -25 to -27 dBm | < -28 dBm |
| **TX Power** | +2 to +5 dBm | < +1 dBm | < 0 dBm |
| **Optic Temperature** | 40-60°C | 60-70°C | > 70°C |
| **CPU Temperature** | 40-70°C | 70-85°C | > 85°C |
| **Voltage** | 3.2-3.4V | 3.0-3.2V or 3.4-3.5V | < 3.0V or > 3.5V |
| **TX Bias Current** | 4-15 mA | 15-20 mA | > 20 mA |
| **Memory Usage** | < 70% | 70-85% | > 85% |
| **PON State** | O5.1 (Associated) | O5.2 (Pending) | O1-O4, O6, O7 |

---

## Optical Power Metrics

### RX Power (Receive Power)

**What it measures:** The optical signal strength your ONU receives from the ISP's OLT (Optical Line Terminal).

**Units:** dBm (decibels relative to 1 milliwatt). More negative = weaker signal.

| Reading | Status | What It Means |
|---------|--------|---------------|
| -10 to -15 dBm | Excellent | Very strong signal, close to OLT |
| -15 to -22 dBm | Good | Ideal operating range |
| -22 to -25 dBm | Acceptable | Normal for longer fiber runs |
| -25 to -27 dBm | Marginal | Signal getting weak, may see occasional errors |
| < -28 dBm | Critical | Link will flap, expect disconnects |
| -40 dBm | No Signal | Fiber disconnected or broken |

**If you see low RX power (-26 dBm or worse):**
1. Clean fiber connectors with a fiber cleaner
2. Check for tight bends or kinks in the fiber cable
3. Verify using SC/APC (green) connectors, not SC/UPC (blue)
4. Check the fiber patch cable for damage
5. Contact ISP if issue persists - may be an outside plant problem

**If you see very high RX power (> -10 dBm):**
- You may be very close to the OLT
- Consider installing a 10 dB attenuator to prevent receiver saturation

### TX Power (Transmit Power)

**What it measures:** The optical signal strength your ONU transmits upstream to the ISP.

| Reading | Status | What It Means |
|---------|--------|---------------|
| +4 to +6 dBm | Excellent | Healthy laser, plenty of headroom |
| +2 to +4 dBm | Good | Normal operating range |
| +1 to +2 dBm | Acceptable | Lower end of normal |
| < +1 dBm | Warning | Laser may be degrading |
| < 0 dBm | Critical | Laser failing, replace module |
| -40 dBm | Dead | Laser burned out |

**If you see low or dropping TX power:**
1. Check temperature - overheating causes TX power drop
2. Add cooling (fan, heatsink) to the SFP module
3. Check power supply voltage
4. If persistent, the laser is aging - plan for replacement

**If you see fluctuating TX power:**
- Usually thermal related
- WAS-110 modules run hot and need active cooling
- Temperature changes cause TX power variations

---

## Temperature Metrics

### Optic Temperature

**What it measures:** Temperature of the SFP transceiver's optical components (laser/photodiode).

| Reading | Status | Notes |
|---------|--------|-------|
| 40-55°C | Normal | Healthy operating temperature |
| 55-60°C | Warm | Within spec but monitor |
| 60-70°C | Warning | WAS-110 runs hot, add cooling |
| > 70°C | Critical | Risk of TX power degradation, reduced lifespan |

**If optic temperature is high:**
1. Ensure adequate airflow around the SFP port
2. Add a small fan pointing at the module
3. Consider a heatsink on the SFP body
4. Don't place in enclosed spaces without ventilation

### CPU Temperature

**What it measures:** Temperature of the ONU's embedded processor.

| Reading | Status | Notes |
|---------|--------|-------|
| 40-60°C | Normal | Healthy operation |
| 60-70°C | Warm | Acceptable under load |
| 70-85°C | Warning | May cause performance issues |
| > 85°C | Critical | Thermal throttling likely |

**If CPU temperature is high:**
- Same remediation as optic temperature
- CPU temp usually follows optic temp trends

---

## Electrical Metrics

### Voltage (VCC)

**What it measures:** Power supply voltage to the SFP transceiver. Should be stable around 3.3V.

| Reading | Status | What It Means |
|---------|--------|---------------|
| 3.2-3.4V | Normal | Healthy power supply |
| 3.0-3.2V | Low Warning | Check power adapter |
| 3.4-3.5V | High Warning | Unusual, check adapter |
| < 3.0V | Critical | Insufficient power, laser may underperform |
| > 3.5V | Critical | Risk of component damage |

**If voltage is abnormal:**
- Check the power adapter specifications
- Verify stable power source (not overloaded power strip)
- Try a different power adapter

### TX Bias Current

**What it measures:** Electrical current driving the laser. Increases over time as laser ages.

| Reading | Status | What It Means |
|---------|--------|---------------|
| 4-10 mA | Normal | Healthy laser |
| 10-15 mA | Acceptable | Normal for some modules |
| 15-20 mA | Elevated | Laser compensating for aging |
| > 20 mA | Warning | Laser end-of-life approaching |

**Understanding TX Bias:**
- The laser driver automatically increases bias current to maintain constant TX power
- Rising bias current over months/years indicates laser aging
- Sudden jumps may indicate thermal stress
- Track this value over time as a "laser health" indicator

---

## System Metrics

### Memory Usage

**What it measures:** RAM utilization on the embedded Linux system.

| Reading | Status | Notes |
|---------|--------|-------|
| < 50% | Normal | Plenty of headroom |
| 50-70% | Acceptable | Normal operation |
| 70-85% | Warning | May indicate memory leak |
| > 85% | Critical | System instability possible |

**If memory is high:**
- Reboot the ONU to clear memory
- If persistently high after reboot, may be firmware issue
- Check for firmware updates

### ONU Uptime

**What it measures:** Time since last reboot in seconds.

**What to look for:**
- Low uptime with no user reboot = unexpected reset
- Track correlation between resets and error events
- Frequent resets may indicate power issues or thermal problems

### Ethernet Speed

**What it measures:** Negotiated speed on the eth0_0 interface.

| Reading | What It Means |
|---------|---------------|
| 10000 Mbps | 10 Gbps - Full XGS-PON speed |
| 2500 Mbps | 2.5 Gbps - Common for some routers |
| 1000 Mbps | 1 Gbps - Limiting your connection |

**If speed is lower than expected:**
- Check router/switch port capabilities
- Verify cable quality (Cat6 or better for 10G)
- Check for auto-negotiation issues

---

## PON State

### Understanding PON States

The ONU goes through a state machine when connecting to the ISP's network.

| Code | State | What It Means |
|------|-------|---------------|
| 10 | O1 - Initial | Just powered on, searching for signal |
| 11 | O1.1 - Off-sync | Lost synchronization, searching |
| 20 | O2 - Stand-by | Found signal, waiting for OLT |
| 23 | O2.3 - Serial Number | Sending serial number to OLT |
| 30 | O3 - Serial Number | Authentication in progress |
| 40 | O4 - Ranging | Measuring distance/timing to OLT |
| **50** | **O5 - Operation** | **Connected and working** |
| **51** | **O5.1 - Associated** | **Normal operation - this is good!** |
| 52 | O5.2 - Pending | Connected but waiting for config |
| 60 | O6 - Intermittent LOS | Lost signal, trying to recover |
| 70 | O7 - Emergency Stop | Disabled by OLT (rogue ONU protection) |

**Normal operation:** You want to see **O5.1 (Associated)** - state code 51.

**If stuck in O1-O4:**
- O1: Check fiber connection, cleaning, signal levels
- O2/O3: Authentication issue - verify serial number matches ISP records
- O4: Ranging failed - may be distance or timing issue

**If you see O6 (Intermittent LOS):**
- Temporary signal loss
- Should return to O5 quickly
- If frequent, check fiber connections

**If you see O7 (Emergency Stop):**
- OLT has disabled your ONU
- May happen if serial number is rejected
- Contact ISP or verify configuration

### Previous State

Shows the state before the current one. Useful for diagnosing:
- What state the ONU was in before reaching O5
- If transitioning between O5 and O6 repeatedly = intermittent signal

### Time in State

How long the ONU has been in the current state (seconds).
- Long time in O5.1 = stable connection
- Short times with state changes = unstable link

---

## GTC Diagnostics (Error Counters)

These counters track errors at the GTC (GPON Transmission Convergence) layer.

### BIP Errors (Bit Interleaved Parity)

**What it measures:** Bit errors detected in downstream traffic using parity checking.

| Count | Meaning |
|-------|---------|
| 0 | Perfect - no errors detected |
| Low (< 100/day) | Minor noise, usually acceptable |
| High (> 1000/day) | Signal quality issue, investigate |

**If BIP errors are increasing:**
1. Check RX power levels
2. Clean fiber connectors
3. Look for fiber damage
4. Contact ISP if outside plant issue suspected

### FEC Corrected

**What it measures:** Forward Error Correction codewords that had errors but were successfully corrected.

| Count | Meaning |
|-------|---------|
| 0-Low | Good signal quality |
| Moderate | FEC is working, some line noise |
| High | Signal marginal but FEC compensating |

**Note:** FEC corrected counts are informational. The errors were fixed automatically. High counts indicate the link is working harder to maintain quality.

### FEC Uncorrected

**What it measures:** Errors that Forward Error Correction could NOT fix. These cause actual data loss.

| Count | Meaning |
|-------|---------|
| 0 | Perfect - all errors corrected |
| Any increase | **Concerning** - data corruption occurring |
| Steadily increasing | **Critical** - link quality degrading |

**If FEC uncorrected is increasing:**
- This is the most serious error counter
- Indicates errors beyond FEC's correction capability (> 8 bit errors per block)
- Check all physical connections
- Verify RX power is in acceptable range
- Contact ISP for line testing

### LODS Events (Loss of Downstream Sync)

**What it measures:** Number of times the ONU lost synchronization with the OLT.

| Count | Meaning |
|-------|---------|
| 0 | Stable connection |
| Occasional (< 1/day) | Minor, possibly power fluctuation |
| Frequent (> 10/day) | **Problem** - investigate signal issues |

**If LODS is increasing:**
- Each LODS event means a brief disconnect
- ONU transitions to O6 state then back to O5
- Check for intermittent signal issues
- May indicate loose connector or fiber damage

---

## Device Information

### ISP

Detected from the GPON serial number prefix. Shows which ISP provisioned the serial.

| Prefix | ISP |
|--------|-----|
| HUMA | AT&T (Humax gateway) |
| NOKA | AT&T (Nokia gateway) |
| COMM | AT&T (CommScope gateway) |
| FTRO | Frontier |
| ALCL | Bell Canada |
| SMBS | Bell Canada (Sagemcom) |

### Module Type

The SFP module type detected (e.g., WAS-110, BFW SFP+).

### PON Mode

Operating mode of the PON network:
- **XGS-PON**: 10G symmetric (most common for new deployments)
- **XG-PON**: 10G down / 2.5G up
- **GPON**: 2.5G down / 1.25G up (older networks)

### Firmware Bank

Which firmware bank is active (A or B). ONU typically has dual banks for safe upgrades.

---

## Troubleshooting Flowchart

```
Link Problems?
├── Check PON State
│   ├── O5.1 → Link OK, check speeds
│   ├── O1-O4 → Authentication issue
│   │   └── Verify serial number, contact ISP
│   ├── O6 → Signal loss events
│   │   └── Check fiber, connectors, RX power
│   └── O7 → Disabled by OLT
│       └── Contact ISP
│
├── RX Power OK? (-15 to -25 dBm)
│   ├── Too low (<-27) → Clean connectors, check cable
│   └── No signal (-40) → Fiber disconnected
│
├── Errors increasing?
│   ├── BIP/FEC Corrected → Signal marginal
│   ├── FEC Uncorrected → Critical, check fiber
│   └── LODS → Intermittent signal
│
└── Performance issues?
    ├── High temperature → Add cooling
    ├── Low TX power → Overheating or aging laser
    └── Low voltage → Check power supply
```

---

## Additional Resources

- [PON.wiki WAS-110 Documentation](https://pon.wiki/xgs-pon/ont/bfw-solutions/was-110/)
- [8311 Community GitHub](https://github.com/up-n-atom/8311)
- [Hack GPON - Authentication States](https://hack-gpon.org/gpon-auth/)
- [ITU-T G.9807.1 XGS-PON Standard](https://www.itu.int/rec/T-REC-G.9807.1)

---

## Contributing

Found an error or have additional insights? Open a PR or issue on GitHub.
