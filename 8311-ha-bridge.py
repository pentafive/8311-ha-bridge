#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
8311 HA Bridge - WAS-110 XGS-PON ONU to Home Assistant MQTT Bridge
Version: 1.0.0
Author: pentafive
Based on: Gemini session research + Claude architecture

Monitors BFW Solutions WAS-110 fiber optic statistics and publishes to Home Assistant
"""

import paho.mqtt.client as mqtt
import base64
import json
import time
import re
import sys
import math
import threading
import subprocess
from datetime import datetime, timezone
from collections import defaultdict

# ==============================================================================
# --- Configuration ---
# ==============================================================================
print("--- Loading Configuration ---")

# --- WAS-110 Device Settings ---
WAS_110_HOST = "192.168.11.1"       # <-- CHANGE THIS to your WAS-110 IP
WAS_110_USER = "root"               # SSH username
WAS_110_PASS = ""                   # SSH password (empty or "Aa123456")
WAS_110_PORT = 22                   # SSH port

# --- Home Assistant MQTT Broker Configuration ---
HA_MQTT_BROKER = "homeassistant.local"    # <-- CHANGE THIS to your MQTT broker IP or hostname
HA_MQTT_PORT = 1883                 # MQTT port
HA_MQTT_USER = "8311-ha-bridge"                 # MQTT username (or None)
HA_MQTT_PASS = None                 # MQTT password (or None) - SET THIS for your broker

# --- Script Operation Settings ---
POLL_INTERVAL_SECONDS = 60          # How often to query WAS-110
SSH_TIMEOUT_SECONDS = 10            # SSH command timeout
RECONNECT_DELAYS = [5, 10, 30, 60]  # Exponential backoff (seconds)
HA_DISCOVERY_PREFIX = "homeassistant"
HA_ENTITY_BASE = "8311"
DEBUG_MODE = True                  # Set to True for verbose logging
TEST_MODE = False                    # Set to True to run a single test cycle instead of monitoring
VERSION = "1.0.1"  # Fix SSH status timing bug

# ==============================================================================
# --- Global Variables ---
# ==============================================================================

ha_mqtt_client = None
device_serial = "unknown"
device_info = {}
stop_event = threading.Event()

# Statistics tracking
stats = {
    'start_time': time.time(),
    'total_updates': 0,
    'total_errors': 0,
    'consecutive_errors': 0,
    'ssh_reconnections': 0,
    'last_error': None,
    'last_error_time': None,
    'update_durations': []
}

# PON State mapping
PON_STATES = {
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

# ==============================================================================
# --- Helper Functions ---
# ==============================================================================

def debug_log(message):
    """Print debug messages if DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[DEBUG {timestamp}] {message}")

def sanitize_for_mqtt(text):
    """Sanitize strings for MQTT topic/entity ID compatibility"""
    if text is None:
        return "unknown"
    sanitized = str(text).replace(".", "_").replace("/", "_")
    sanitized = sanitized.replace("#", "").replace("+", "")
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', sanitized)
    return sanitized.lower()

def watts_to_dbm(mw):
    """Convert milliwatts to dBm"""
    if mw <= 0:
        return -100.0
    return round(10 * math.log10(mw), 2)

def get_iso_timestamp():
    """Get current timestamp in ISO 8601 format"""
    return datetime.now(timezone.utc).isoformat()

def get_pon_state_name(state_code):
    """Get human-readable PON state name"""
    return PON_STATES.get(state_code, f"Unknown state {state_code}")

# ==============================================================================
# --- Data Parsing Functions ---
# ==============================================================================

def parse_eeprom51(raw_bytes):
    """
    Parse EEPROM51 for real-time optical diagnostics
    Based on 8311.lua action_gpon_status function
    """
    metrics = {}

    if len(raw_bytes) < 106:
        debug_log(f"EEPROM51 too short: {len(raw_bytes)} bytes")
        return metrics

    try:
        # Optic Temperature (Bytes 96-97)
        metrics['optic_temp'] = round(raw_bytes[96] + (raw_bytes[97] / 256.0), 2)

        # Voltage (Bytes 98-99)
        metrics['voltage'] = round(((raw_bytes[98] << 8) + raw_bytes[99]) / 10000.0, 3)

        # TX Bias (Bytes 100-101)
        metrics['tx_bias'] = round(((raw_bytes[100] << 8) + raw_bytes[101]) / 500.0, 2)

        # TX Power (Bytes 102-103) -> mW
        tx_mw = ((raw_bytes[102] << 8) + raw_bytes[103]) / 10000.0
        metrics['tx_power_mw'] = round(tx_mw, 4)
        metrics['tx_power_dbm'] = watts_to_dbm(tx_mw)

        # RX Power (Bytes 104-105) -> mW
        rx_mw = ((raw_bytes[104] << 8) + raw_bytes[105]) / 10000.0
        metrics['rx_power_mw'] = round(rx_mw, 4)
        metrics['rx_power_dbm'] = watts_to_dbm(rx_mw)

        debug_log(f"EEPROM51 parsed: RX={metrics['rx_power_dbm']}dBm, TX={metrics['tx_power_dbm']}dBm, Temp={metrics['optic_temp']}°C")

    except Exception as e:
        debug_log(f"Error parsing EEPROM51: {e}")

    return metrics

def parse_eeprom50(raw_bytes):
    """
    Parse EEPROM50 for static device information
    Based on 8311.lua action_gpon_status function
    """
    info = {}

    if len(raw_bytes) < 60:
        debug_log(f"EEPROM50 too short: {len(raw_bytes)} bytes")
        return info

    try:
        # Vendor Name (Bytes 20-35)
        info['vendor_name'] = raw_bytes[20:36].decode('ascii', errors='ignore').strip()

        # Part Number (Bytes 40-55)
        info['part_number'] = raw_bytes[40:56].decode('ascii', errors='ignore').strip()

        # Revision (Bytes 56-59)
        info['revision'] = raw_bytes[56:60].decode('ascii', errors='ignore').strip()

        debug_log(f"EEPROM50 parsed: {info['vendor_name']} {info['part_number']} {info['revision']}")

    except Exception as e:
        debug_log(f"Error parsing EEPROM50: {e}")

    return info

def parse_pon_status(output):
    """Parse PON state from 'pon psg' command output"""
    state_match = re.search(r'current=(\d+)', output)
    time_match = re.search(r'time_curr=(\d+)', output)

    if state_match:
        state_code = int(state_match.group(1))
        time_in_state = int(time_match.group(1)) if time_match else 0

        # Format duration as human-readable
        hours = time_in_state // 3600
        minutes = (time_in_state % 3600) // 60
        seconds = time_in_state % 60
        time_formatted = f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s"

        return {
            'state_code': state_code,
            'state_name': get_pon_state_name(state_code),
            'link_up': state_code in [50, 51, 52],  # O5 states = operational
            'time_in_state_seconds': time_in_state,
            'time_in_state_formatted': time_formatted
        }
    return None

# ==============================================================================
# --- SSH Connection ---
# ==============================================================================

def check_host_reachable():
    """
    Checks if the WAS-110 host is reachable via ICMP ping.
    This is useful because the device may respond to ping even when SSH is temporarily unresponsive.
    Returns True if host responds to ping, False otherwise.
    """
    try:
        # Use -c 1 for single ping, -W timeout in seconds
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", WAS_110_HOST],
            capture_output=True,
            timeout=3
        )

        if result.returncode == 0:
            debug_log(f"Host {WAS_110_HOST} is reachable via ping")
            return True
        else:
            debug_log(f"Host {WAS_110_HOST} did not respond to ping")
            return False

    except subprocess.TimeoutExpired:
        debug_log(f"Ping to {WAS_110_HOST} timed out")
        return False
    except Exception as e:
        debug_log(f"Error checking host reachability: {e}")
        return False

def execute_ssh_command(command):
    """
    Executes a command on the remote device using the system's native 'ssh' command
    via a subprocess. This method was chosen over the `paramiko` library after
    extensive debugging revealed authentication issues between `paramiko` and the
    Dropbear SSH server on the WAS-110 device.

    The key findings were:
    1. `paramiko`'s password authentication was rejected by the server.
    2. `paramiko`'s public key authentication failed on an encrypted key.
    3. The native `ssh` client connected successfully without a password, likely
       using keyboard-interactive authentication.

    This `subprocess` approach leverages the known-working system `ssh` client,
    ensuring reliable, non-interactive execution suitable for a container.
    The `-o StrictHostKeyChecking=no` and `-o UserKnownHostsFile=/dev/null` options
    are used to automatically handle host key verification without user prompts.
    """
    ssh_command = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=" + str(SSH_TIMEOUT_SECONDS),
        f"{WAS_110_USER}@{WAS_110_HOST}",
        command
    ]

    try:
        debug_log(f"Executing SSH command: {' '.join(ssh_command)}")
        result = subprocess.run(
            ssh_command,
            capture_output=True,
            timeout=SSH_TIMEOUT_SECONDS
        )

        if result.returncode == 0:
            return result.stdout
        else:
            error_message = result.stderr.decode('utf-8', errors='ignore').strip()
            print(f"✗ SSH command failed with return code {result.returncode}: {error_message}")
            stats['total_errors'] += 1
            stats['consecutive_errors'] += 1
            stats['last_error'] = f"SSH command failed: {error_message}"
            stats['last_error_time'] = get_iso_timestamp()
            return None

    except subprocess.TimeoutExpired:
        error_message = f"SSH command timed out after {SSH_TIMEOUT_SECONDS} seconds."
        print(f"✗ {error_message}")
        stats['total_errors'] += 1
        stats['consecutive_errors'] += 1
        stats['last_error'] = error_message
        stats['last_error_time'] = get_iso_timestamp()
        return None
    except Exception as e:
        error_message = f"SSH subprocess execution failed: {e}"
        print(f"✗ {error_message}")
        stats['total_errors'] += 1
        stats['consecutive_errors'] += 1
        stats['last_error'] = error_message
        stats['last_error_time'] = get_iso_timestamp()
        return None

def connect_ssh():
    """
    Tests the SSH connection by first checking host reachability via ping,
    then executing a simple 'echo' command via SSH.
    Returns True if successful, False otherwise.
    """
    print(f"Connecting to WAS-110 at {WAS_110_HOST}...")

    # First check if host is reachable via ping
    if not check_host_reachable():
        print(f"✗ Host {WAS_110_HOST} is not responding to ping")
        if not TEST_MODE:
            publish_binary_sensor_state("ssh_connection_status", False)
        return False

    print(f"✓ Host is reachable, attempting SSH connection...")

    # Now try SSH connection
    if execute_ssh_command("echo 'SSH connection successful'") is not None:
        print("✓ SSH connection appears to be working.")
        if not TEST_MODE:
            publish_binary_sensor_state("ssh_connection_status", True)
        return True
    else:
        print("✗ SSH connection test failed (but host responds to ping).")
        if not TEST_MODE:
            publish_binary_sensor_state("ssh_connection_status", False)
        return False

# ==============================================================================
# --- MQTT Connection ---
# ==============================================================================

def on_connect_ha(client, userdata, flags, rc, properties=None):
    """Callback when connected to Home Assistant MQTT broker"""
    if rc == 0:
        print("✓ Connected to Home Assistant MQTT broker")
    else:
        print(f"✗ Failed to connect to MQTT broker, return code {rc}")

def on_disconnect_ha(client, userdata, flags, rc, properties=None):
    """Callback when disconnected from HA MQTT broker"""
    if rc != 0:
        print(f"⚠ Unexpected MQTT disconnect, return code {rc}")

def connect_mqtt():
    """Connect to Home Assistant MQTT broker"""
    global ha_mqtt_client

    print(f"Connecting to MQTT broker at {HA_MQTT_BROKER}:{HA_MQTT_PORT}...")

    ha_mqtt_client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="8311-ha-bridge"
    )

    ha_mqtt_client.on_connect = on_connect_ha
    ha_mqtt_client.on_disconnect = on_disconnect_ha

    if HA_MQTT_USER and HA_MQTT_PASS:
        ha_mqtt_client.username_pw_set(HA_MQTT_USER, HA_MQTT_PASS)

    try:
        ha_mqtt_client.connect(HA_MQTT_BROKER, HA_MQTT_PORT, 60)
        ha_mqtt_client.loop_start()

        # Wait for connection to be established
        timeout = 10  # seconds
        start_time = time.time()
        while not ha_mqtt_client.is_connected() and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        if not ha_mqtt_client.is_connected():
            print("✗ MQTT connection timeout")
            return False

        return True
    except Exception as e:
        print(f"✗ MQTT connection failed: {e}")
        return False

def publish_mqtt(topic, payload, retain=False, qos=0):
    """Publish message to MQTT broker"""
    global ha_mqtt_client

    if ha_mqtt_client is None:
        return False

    try:
        if isinstance(payload, dict):
            payload = json.dumps(payload)

        result = ha_mqtt_client.publish(topic, payload, qos=qos, retain=retain)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            debug_log(f"Published to {topic}: {len(str(payload))} bytes")
            return True
        else:
            print(f"✗ MQTT publish failed to {topic}, rc={result.rc}")
            return False

    except Exception as e:
        print(f"✗ MQTT publish exception: {e}")
        return False

# ==============================================================================
# --- Home Assistant Discovery ---
# ==============================================================================

def get_device_config():
    """Generate device configuration for MQTT discovery"""
    global device_serial, device_info

    device_id = f"8311_onu_{sanitize_for_mqtt(device_serial)}"

    sw_version = "8311 Community"
    if 'firmware_bank' in device_info:
        sw_version += f" (Bank {device_info['firmware_bank']})"

    return {
        "identifiers": [device_id],
        "name": f"8311 ONU ({device_serial})",
        "manufacturer": device_info.get('vendor_name', 'BFW Solutions'),
        "model": device_info.get('part_number', 'WAS-110'),
        "sw_version": sw_version,
        "via_device": "8311-ha-bridge",
        "configuration_url": f"https://{WAS_110_HOST}"
    }

def publish_sensor_discovery(sensor_id, sensor_name, unit=None, device_class=None, icon=None, state_class=None):
    """Publish MQTT discovery config for a sensor"""
    device_id = f"8311_onu_{sanitize_for_mqtt(device_serial)}"
    unique_id = f"{device_id}_{sensor_id}"

    config = {
        "name": sensor_name,
        "unique_id": unique_id,
        "state_topic": f"{HA_ENTITY_BASE}/sensor/{device_id}/{sensor_id}/state",
        "json_attributes_topic": f"{HA_ENTITY_BASE}/sensor/{device_id}/{sensor_id}/attributes",
        "device": get_device_config()
    }

    if unit:
        config["unit_of_measurement"] = unit
    if device_class:
        config["device_class"] = device_class
    if icon:
        config["icon"] = icon
    if state_class:
        config["state_class"] = state_class

    discovery_topic = f"{HA_DISCOVERY_PREFIX}/sensor/{device_id}/{sensor_id}/config"
    publish_mqtt(discovery_topic, config, retain=True, qos=1)
    time.sleep(0.05)

def publish_binary_sensor_discovery(sensor_id, sensor_name, device_class=None, icon=None):
    """Publish MQTT discovery config for a binary sensor"""
    device_id = f"8311_onu_{sanitize_for_mqtt(device_serial)}"
    unique_id = f"{device_id}_{sensor_id}"

    config = {
        "name": sensor_name,
        "unique_id": unique_id,
        "state_topic": f"{HA_ENTITY_BASE}/binary_sensor/{device_id}/{sensor_id}/state",
        "json_attributes_topic": f"{HA_ENTITY_BASE}/binary_sensor/{device_id}/{sensor_id}/attributes",
        "payload_on": "ON",
        "payload_off": "OFF",
        "device": get_device_config()
    }

    if device_class:
        config["device_class"] = device_class
    if icon:
        config["icon"] = icon

    discovery_topic = f"{HA_DISCOVERY_PREFIX}/binary_sensor/{device_id}/{sensor_id}/config"
    publish_mqtt(discovery_topic, config, retain=True, qos=1)
    time.sleep(0.05)

# ==============================================================================
# --- Sensor Publishing ---
# ==============================================================================

def publish_sensor_state(sensor_id, value, attributes=None):
    """Publish sensor state and attributes"""
    device_id = f"8311_onu_{sanitize_for_mqtt(device_serial)}"

    state_topic = f"{HA_ENTITY_BASE}/sensor/{device_id}/{sensor_id}/state"
    publish_mqtt(state_topic, str(value), qos=1)

    if attributes:
        attr_topic = f"{HA_ENTITY_BASE}/sensor/{device_id}/{sensor_id}/attributes"
        publish_mqtt(attr_topic, attributes, qos=1)

def publish_binary_sensor_state(sensor_id, value, attributes=None):
    """Publish binary sensor state and attributes"""
    device_id = f"8311_onu_{sanitize_for_mqtt(device_serial)}"

    state_topic = f"{HA_ENTITY_BASE}/binary_sensor/{device_id}/{sensor_id}/state"
    publish_mqtt(state_topic, "ON" if value else "OFF", qos=1)

    if attributes:
        attr_topic = f"{HA_ENTITY_BASE}/binary_sensor/{device_id}/{sensor_id}/attributes"
        publish_mqtt(attr_topic, attributes, qos=1)

# ==============================================================================
# --- Data Collection ---
# ==============================================================================

def collect_device_info():
    """
    Collect static device information (run once at startup)

    Uses a single SSH session with combined commands to avoid rate limiting.
    """
    global device_info, device_serial

    print("\n📋 Collecting device information...")

    try:
        # Execute all commands in a single SSH session
        combined_command = (
            "cat /sys/class/pon_mbox/pon_mbox0/device/eeprom50 | base64 && "
            "echo '===DELIMITER===' && "
            "uci get gpon.ponip.pon_mode 2>/dev/null || echo unknown && "
            "echo '===DELIMITER===' && "
            ". /lib/8311.sh && active_fwbank 2>/dev/null || echo unknown"
        )

        combined_output = execute_ssh_command(combined_command)

        if not combined_output:
            print("⚠ Could not retrieve device info via SSH")
            return False

        # Split output by delimiter
        outputs = combined_output.decode('utf-8', errors='ignore').split('===DELIMITER===')

        if len(outputs) < 3:
            print(f"⚠ Expected 3 output sections, got {len(outputs)}")
            return False

        # Part 1: Get EEPROM50 data
        eep50_b64_raw = outputs[0].strip()
        if eep50_b64_raw:
            try:
                eep50_bytes = base64.b64decode(eep50_b64_raw)
                eep50_data = parse_eeprom50(eep50_bytes)
                device_info.update(eep50_data)
            except Exception as e:
                print(f"⚠ Could not parse EEPROM50: {e}")
        else:
            print("⚠ Could not retrieve EEPROM50 info.")

        # Part 2: Get PON mode
        pon_mode_raw = outputs[1].strip().upper()
        if pon_mode_raw and pon_mode_raw != 'UNKNOWN':
            if 'PON' in pon_mode_raw:
                pon_mode_raw = pon_mode_raw.replace('PON', '-PON')
            device_info['pon_mode'] = pon_mode_raw
        else:
            device_info['pon_mode'] = 'Unknown'

        # Part 3: Get active firmware bank
        fw_bank_raw = outputs[2].strip()
        if fw_bank_raw and fw_bank_raw.lower() != 'unknown':
            device_info['firmware_bank'] = fw_bank_raw
        else:
            device_info['firmware_bank'] = 'Unknown'

        # Set device serial (use part number + last 4 of vendor name as fallback)
        device_serial = f"WAS110_{device_info.get('part_number', 'unknown')[:6]}"

        print(f"✓ Device: {device_info.get('vendor_name')} {device_info.get('part_number')} Rev {device_info.get('revision')}")
        print(f"✓ PON Mode: {device_info.get('pon_mode')}, Firmware: Bank {device_info.get('firmware_bank')}")

        return True

    except Exception as e:
        print(f"✗ Error parsing device info: {e}")
        return False

def collect_metrics():
    """
    Collect all real-time metrics from WAS-110

    Uses a single SSH session with multiple commands to avoid rate limiting.
    Commands are separated by echo statements to create delimiters for parsing.
    """
    start_time = time.time()
    metrics = {}

    try:
        # Execute all commands in a single SSH session to avoid rate limiting
        # Use echo statements as delimiters to split the output
        combined_command = (
            "cat /sys/class/pon_mbox/pon_mbox0/device/eeprom51 | base64 && "
            "echo '===DELIMITER===' && "
            "cat /sys/class/thermal/thermal_zone0/temp && "
            "echo '===DELIMITER===' && "
            "cat /sys/class/thermal/thermal_zone1/temp && "
            "echo '===DELIMITER===' && "
            "cat /sys/class/net/eth0_0/speed && "
            "echo '===DELIMITER===' && "
            "pon psg"
        )

        combined_output = execute_ssh_command(combined_command)

        if not combined_output:
            debug_log("Combined SSH command failed")
            return None

        # Split output by delimiter
        outputs = combined_output.decode('utf-8', errors='ignore').split('===DELIMITER===')

        if len(outputs) < 5:
            debug_log(f"Expected 5 output sections, got {len(outputs)}")
            return None

        # 1. Parse EEPROM51 (optical metrics)
        eep51_b64_raw = outputs[0].strip()
        if eep51_b64_raw:
            try:
                eep51_bytes = base64.b64decode(eep51_b64_raw)
                optical_metrics = parse_eeprom51(eep51_bytes)
                metrics.update(optical_metrics)
            except Exception as e:
                debug_log(f"Error parsing EEPROM51: {e}")

        # 2. Parse CPU0 temp
        cpu0_temp_raw = outputs[1].strip()
        if cpu0_temp_raw:
            try:
                metrics['cpu0_temp'] = round(int(cpu0_temp_raw) / 1000.0, 1)
            except (ValueError, TypeError):
                debug_log("Could not parse CPU0 temp")

        # 3. Parse CPU1 temp
        cpu1_temp_raw = outputs[2].strip()
        if cpu1_temp_raw:
            try:
                metrics['cpu1_temp'] = round(int(cpu1_temp_raw) / 1000.0, 1)
            except (ValueError, TypeError):
                debug_log("Could not parse CPU1 temp")

        # 4. Parse ethernet speed
        eth_speed_raw = outputs[3].strip()
        if eth_speed_raw:
            try:
                metrics['eth_speed'] = int(eth_speed_raw)
            except (ValueError, TypeError):
                debug_log("Could not parse eth speed")

        # 5. Parse PON status
        pon_status_raw = outputs[4].strip()
        if pon_status_raw:
            pon_status = parse_pon_status(pon_status_raw)
            if pon_status:
                metrics['pon_status'] = pon_status

        duration = (time.time() - start_time) * 1000
        stats['update_durations'].append(duration)
        if len(stats['update_durations']) > 100:
            stats['update_durations'].pop(0)

        debug_log(f"Metrics collected in {duration:.0f}ms")
        return metrics

    except Exception as e:
        print(f"✗ Error parsing metrics: {e}")
        stats['total_errors'] += 1
        stats['consecutive_errors'] += 1
        stats['last_error'] = f"Metric parsing error: {str(e)}"
        stats['last_error_time'] = get_iso_timestamp()
        return None

# ==============================================================================
# --- Main Monitoring Loop ---
# ==============================================================================

def publish_all_discovery():
    """Publish discovery configs for all sensors"""
    print("\n📡 Publishing MQTT Auto Discovery configs...")

    # Optical Performance Sensors
    publish_sensor_discovery("rx_power_dbm", "RX Power", "dBm", "signal_strength", "mdi:access-point", "measurement")
    publish_sensor_discovery("rx_power_mw", "RX Power (mW)", "mW", "power", "mdi:access-point", "measurement")
    publish_sensor_discovery("tx_power_dbm", "TX Power", "dBm", "signal_strength", "mdi:access-point", "measurement")
    publish_sensor_discovery("tx_power_mw", "TX Power (mW)", "mW", "power", "mdi:access-point", "measurement")
    publish_sensor_discovery("voltage", "Voltage", "V", "voltage", "mdi:flash", "measurement")
    publish_sensor_discovery("tx_bias", "TX Bias Current", "mA", "current", "mdi:current-ac", "measurement")

    # Temperature Sensors
    publish_sensor_discovery("optic_temperature", "Optic Temperature", "°C", "temperature", "mdi:thermometer-laser", "measurement")
    publish_sensor_discovery("cpu0_temperature", "CPU0 Temperature", "°C", "temperature", "mdi:chip", "measurement")
    publish_sensor_discovery("cpu1_temperature", "CPU1 Temperature", "°C", "temperature", "mdi:chip", "measurement")

    # Link Status Binary Sensors
    publish_binary_sensor_discovery("pon_link_status", "PON Link", "connectivity", "mdi:fiber-optic")
    publish_binary_sensor_discovery("ssh_connection_status", "SSH Connection", "connectivity", "mdi:lan-connect")

    # Network Performance
    publish_sensor_discovery("ethernet_speed", "Ethernet Speed", "Mbps", None, "mdi:ethernet", "measurement")

    # Device Information Sensors
    publish_sensor_discovery("vendor_name", "Vendor", None, None, "mdi:factory")
    publish_sensor_discovery("part_number", "Part Number", None, None, "mdi:barcode")
    publish_sensor_discovery("hardware_revision", "Hardware Revision", None, None, "mdi:chip")
    publish_sensor_discovery("pon_mode", "PON Mode", None, None, "mdi:wan")
    publish_sensor_discovery("firmware_bank", "Active Firmware Bank", None, None, "mdi:alphabet-latin")

    # System Statistics
    publish_sensor_discovery("bridge_uptime", "Bridge Uptime", "s", "duration", "mdi:timer-outline", "total_increasing")

    print("✓ Discovery configs published\n")

def monitor_was_110():
    """Main monitoring loop"""
    global device_info, stats

    print("\n=== Starting WAS-110 Monitoring ===\n")

    # Collect device info once at startup
    if not collect_device_info():
        print("⚠ Continuing with limited device info...")

    # Publish all discovery configs
    publish_all_discovery()

    # Publish static device info sensors
    timestamp = get_iso_timestamp()
    publish_sensor_state("vendor_name", device_info.get('vendor_name', 'Unknown'), {"last_update": timestamp})
    publish_sensor_state("part_number", device_info.get('part_number', 'Unknown'), {"last_update": timestamp})
    publish_sensor_state("hardware_revision", device_info.get('revision', 'Unknown'), {"last_update": timestamp})
    publish_sensor_state("pon_mode", device_info.get('pon_mode', 'Unknown'), {"last_update": timestamp})
    publish_sensor_state("firmware_bank", device_info.get('firmware_bank', 'Unknown'), {"last_update": timestamp})

    # FIX: Re-publish SSH status after discovery configs are sent
    # This ensures Home Assistant receives initial state AFTER entity exists
    publish_binary_sensor_state("ssh_connection_status", True, {
        "last_update": timestamp,
        "source": "post_discovery_sync"
    })
    debug_log("Re-published SSH connection status after discovery configs")

    print("📊 Entering monitoring loop (Ctrl+C to stop)...\n")

    # Main monitoring loop
    while not stop_event.is_set():
        try:
            timestamp = get_iso_timestamp()

            # Collect metrics
            metrics = collect_metrics()

            if metrics:
                # Publish optical metrics
                if 'rx_power_dbm' in metrics:
                    publish_sensor_state("rx_power_dbm", metrics['rx_power_dbm'], {"last_update": timestamp, "source": "eeprom51"})
                if 'rx_power_mw' in metrics:
                    publish_sensor_state("rx_power_mw", metrics['rx_power_mw'], {"last_update": timestamp, "source": "eeprom51"})
                if 'tx_power_dbm' in metrics:
                    publish_sensor_state("tx_power_dbm", metrics['tx_power_dbm'], {"last_update": timestamp, "source": "eeprom51"})
                if 'tx_power_mw' in metrics:
                    publish_sensor_state("tx_power_mw", metrics['tx_power_mw'], {"last_update": timestamp, "source": "eeprom51"})
                if 'voltage' in metrics:
                    publish_sensor_state("voltage", metrics['voltage'], {"last_update": timestamp, "source": "eeprom51"})
                if 'tx_bias' in metrics:
                    publish_sensor_state("tx_bias", metrics['tx_bias'], {"last_update": timestamp, "source": "eeprom51"})

                # Publish temperature metrics
                if 'optic_temp' in metrics:
                    temp_f = round(metrics['optic_temp'] * 1.8 + 32, 1)
                    publish_sensor_state("optic_temperature", metrics['optic_temp'], {
                        "last_update": timestamp,
                        "fahrenheit": temp_f,
                        "source": "eeprom51"
                    })
                if 'cpu0_temp' in metrics:
                    temp_f = round(metrics['cpu0_temp'] * 1.8 + 32, 1)
                    publish_sensor_state("cpu0_temperature", metrics['cpu0_temp'], {
                        "last_update": timestamp,
                        "fahrenheit": temp_f
                    })
                if 'cpu1_temp' in metrics:
                    temp_f = round(metrics['cpu1_temp'] * 1.8 + 32, 1)
                    publish_sensor_state("cpu1_temperature", metrics['cpu1_temp'], {
                        "last_update": timestamp,
                        "fahrenheit": temp_f
                    })

                # Publish PON link status
                if 'pon_status' in metrics:
                    pon = metrics['pon_status']
                    publish_binary_sensor_state("pon_link_status", pon['link_up'], {
                        "state_code": pon['state_code'],
                        "state_name": pon['state_name'],
                        "time_in_state_seconds": pon.get('time_in_state_seconds', 0),
                        "time_in_state_formatted": pon.get('time_in_state_formatted', '0s'),
                        "last_update": timestamp
                    })

                # Publish ethernet speed
                if 'eth_speed' in metrics:
                    speed = metrics['eth_speed']
                    speed_gbps = speed / 1000 if speed >= 1000 else 0
                    publish_sensor_state("ethernet_speed", speed, {
                        "last_update": timestamp,
                        "link_detected": speed > 0,
                        "speed_formatted": f"{speed_gbps} Gbps" if speed_gbps > 0 else f"{speed} Mbps"
                    })

                # Update statistics
                stats['total_updates'] += 1
                stats['consecutive_errors'] = 0

                # Publish bridge statistics
                uptime = int(time.time() - stats['start_time'])
                avg_duration = sum(stats['update_durations']) / len(stats['update_durations']) if stats['update_durations'] else 0
                error_rate = (stats['total_errors'] / stats['total_updates'] * 100) if stats['total_updates'] > 0 else 0

                publish_sensor_state("bridge_uptime", uptime, {
                    "total_updates": stats['total_updates'],
                    "total_errors": stats['total_errors'],
                    "consecutive_errors": stats['consecutive_errors'],
                    "error_rate_percent": round(error_rate, 2),
                    "last_update": timestamp,
                    "last_error": stats['last_error'],
                    "last_error_time": stats['last_error_time'],
                    "ssh_reconnections": stats['ssh_reconnections'],
                    "average_update_duration_ms": round(avg_duration, 0),
                    "version": VERSION
                })

                # Periodic SSH status - confirms connection still healthy
                publish_binary_sensor_state("ssh_connection_status", True, {
                    "last_update": timestamp,
                    "consecutive_errors": stats['consecutive_errors'],
                    "source": "monitoring_loop"
                })

                print(f"✓ Update #{stats['total_updates']}: RX={metrics.get('rx_power_dbm', 'N/A')}dBm, TX={metrics.get('tx_power_dbm', 'N/A')}dBm, Temp={metrics.get('optic_temp', 'N/A')}°C, Link={'UP' if metrics.get('pon_status', {}).get('link_up') else 'DOWN'}")

            else:
                print("⚠ Failed to collect metrics")

                # Try to reconnect SSH after consecutive failures
                if stats['consecutive_errors'] >= 3:
                    print("🔄 Attempting SSH reconnection...")
                    if not connect_ssh():
                        print("⚠ SSH reconnection failed, will retry next cycle")
                        stats['ssh_reconnections'] += 1

            # Wait for next poll interval
            stop_event.wait(POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\n⚠ Received keyboard interrupt, shutting down...")
            break
        except Exception as e:
            print(f"✗ Error in monitoring loop: {e}")
            stats['total_errors'] += 1
            stats['consecutive_errors'] += 1
            stats['last_error'] = f"Loop error: {str(e)}"
            stats['last_error_time'] = get_iso_timestamp()
            stop_event.wait(POLL_INTERVAL_SECONDS)

# ==============================================================================
# --- Test Mode ---
# ==============================================================================
def run_test_mode():
    """Connect, fetch metrics once, print to console, and exit."""
    print("\n" + "="*70)
    print("  RUNNING IN TEST MODE")
    print("="*70 + "\n")

    # 1. Connect to MQTT
    print("--- 1. Testing MQTT Connection ---")
    if connect_mqtt():
        print("✓ MQTT Broker Connection: SUCCESS")
        # Wait a moment for connection to establish before disconnecting
        time.sleep(2)
        ha_mqtt_client.disconnect()
        ha_mqtt_client.loop_stop()
    else:
        print("✗ MQTT Broker Connection: FAILED")
    print("-" * 35)


    # 2. Connect to SSH
    print("\n--- 2. Testing SSH Connection ---")
    if not connect_ssh():
        print("✗ SSH Connection: FAILED. Cannot proceed.")
        return
    print("✓ SSH Connection: SUCCESS")
    print("-" * 35)

    # 3. Collect Device Info
    print("\n--- 3. Collecting Device Info ---")
    device_data = collect_device_info()
    if device_data:
        print("✓ Device Info:")
        print(json.dumps(device_info, indent=2))
    else:
        print("✗ Failed to collect device info.")
    print("-" * 35)

    # 4. Collect Metrics
    print("\n--- 4. Collecting Real-time Metrics ---")
    metrics = collect_metrics()
    if metrics:
        print("✓ Collected Metrics:")
        # Manually handle fields that might not be JSON serializable if needed
        print(json.dumps(metrics, indent=2, default=str))
    else:
        print("✗ Failed to collect metrics.")
    print("-" * 35)

    print("\nTest mode finished.")


# ==============================================================================
# --- Main ---
# ==============================================================================

def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("  8311 HA Bridge v{VERSION} - WAS-110 to Home Assistant".replace("{VERSION}", VERSION))
    print("  Based on Gemini research + Claude architecture")
    print("="*70 + "\n")

    if TEST_MODE:
        run_test_mode()
        sys.exit(0)

    # Connect to MQTT broker
    if not connect_mqtt():
        print("✗ Failed to connect to MQTT broker, exiting")
        sys.exit(1)

    # Wait for MQTT connection to stabilize
    time.sleep(2)

    # Connect to WAS-110 via SSH
    if not connect_ssh():
        print("✗ Failed to connect to WAS-110, exiting")
        sys.exit(1)

    # Wait for SSH connection to stabilize
    time.sleep(1)

    try:
        # Start monitoring
        monitor_was_110()
    except KeyboardInterrupt:
        print("\n⚠ Keyboard interrupt received")
    finally:
        # Cleanup
        print("\n🛑 Shutting down...")
        stop_event.set()

        if ha_mqtt_client:
            ha_mqtt_client.loop_stop()
            ha_mqtt_client.disconnect()

        print("✓ Shutdown complete")

if __name__ == "__main__":
    main()
