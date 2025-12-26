# Troubleshooting

Common issues and solutions for 8311 HA Bridge.

## Connection Issues

### Container can't reach WAS-110

**Symptoms:** Logs show "Host 192.168.11.1 is not responding to ping"

**Solutions:**
1. Check gateway alias: `ip addr show <interface> | grep 192.168.11`
2. If missing, restore it: `ip addr add 192.168.11.2/24 dev <interface>`
3. Check Docker host routing: `ip route get 192.168.11.1`
4. Verify WAS-110 is powered and connected

### SSH connection refused

**Symptoms:** Ping works but SSH fails

**Solutions:**
1. WAS-110 may be rate-limiting SSH connections (wait 30 seconds)
2. Access web UI at https://192.168.11.1 to "wake" the device
3. Verify SSH is enabled in 8311 firmware settings
4. Check credentials (default: root with empty password)

### SSH timeouts after multiple connections

**Symptoms:** First connection works, subsequent ones timeout

**Cause:** WAS-110 has aggressive SSH rate limiting

**Solution:** The bridge already combines commands to minimize connections. If still occurring:
- Increase `POLL_INTERVAL_SECONDS` (default: 60)
- Increase `SSH_TIMEOUT_SECONDS` (default: 10)

## MQTT Issues

### No sensors appearing in Home Assistant

**Check:**
1. MQTT broker is running and accessible
2. MQTT credentials are correct
3. MQTT Discovery is enabled in HA (Settings → Devices & Services → MQTT)
4. Discovery prefix matches (default: `homeassistant`)

**Debug:**
```bash
# Check container logs
docker logs 8311-ha-bridge

# Verify MQTT messages with mosquitto_sub
mosquitto_sub -h YOUR_MQTT_BROKER -t "homeassistant/#" -v
```

### Sensors show "unavailable"

**Causes:**
1. Bridge lost connection to WAS-110
2. Bridge lost connection to MQTT broker
3. Container crashed

**Check:**
```bash
docker logs --tail 50 8311-ha-bridge
docker ps | grep 8311
```

## Data Issues

### Incorrect optical power readings

**Symptoms:** Values seem wrong (e.g., -100 dBm constantly)

**Causes:**
1. EEPROM read failed - check SSH connectivity
2. Device in low-power state - access web UI to wake it
3. No fiber connected - check physical connection

### Missing metrics

**Some sensors show data, others don't**

**Check:**
1. Set `DEBUG_MODE=True` to see detailed logs
2. Verify 8311 firmware version supports all metrics
3. Some metrics require specific PON states (e.g., link must be up)

## Gateway-Specific Issues

### Alias keeps disappearing (UniFi)

**Cause:** UniFi controller provisioning removes interface customizations

**Solution:** Use cron-based resilience instead of on-boot scripts. See [[UCG-Fiber-Setup]].

**Monitor:**
```bash
grep "was110-alias" /var/log/messages | tail -10
```

### Silent monitoring failures

**Symptoms:** Container running but no data for hours/days

**Prevention:**
1. Monitor the `bridge_uptime` sensor in HA
2. Create HA automation to alert if `ssh_connection_status` goes offline
3. Check alias restoration logs periodically

## Performance Issues

### High CPU usage

**Cause:** Too frequent polling

**Solution:** Increase `POLL_INTERVAL_SECONDS` (default: 60, try 120)

### Container memory growth

**Cause:** Log accumulation (rare)

**Solution:** Restart container periodically or add log rotation

## Getting Help

1. Check container logs: `docker logs 8311-ha-bridge`
2. Enable debug mode: `DEBUG_MODE=True`
3. Open an issue with logs and configuration (scrub credentials!)
