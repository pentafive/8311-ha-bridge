# Troubleshooting

Common issues and solutions for 8311 HA Bridge.

## HACS Integration Issues

### Integration not appearing after install

**Solutions:**
1. Restart Home Assistant (not just reload)
2. Clear browser cache
3. Check HACS → Integrations → 8311 ONU Monitor is installed

### Sensors showing "Unknown" or "Unavailable"

**Check:**
1. SSH access to ONU: `ssh root@192.168.11.1`
2. Correct password in integration config
3. Network routing to 192.168.11.0/24 subnet

**Debug:**
1. Go to Settings → Devices & Services → 8311 ONU Monitor
2. Click "1 device" → Check device info
3. Enable debug logging:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.was110_8311: debug
```

### PON Link showing "Disconnected" when connected

**Fixed in v2.0.0.** If still occurring:
1. Reload the integration: Settings → Devices & Services → 8311 ONU Monitor → 3 dots → Reload
2. Check diagnostics download for raw state_code value

### New sensors not appearing after update

After updating to v2.0.0:
1. Reload integration (not just HA restart)
2. Check Settings → Devices & Services → 8311 ONU Monitor → device
3. New sensors like ISP, Memory, GTC counters should appear

### Re-authentication required

If credentials change:
1. HA will show "Requires reconfiguration"
2. Click Configure and enter new credentials
3. Integration will reconnect

---

## Docker/MQTT Issues

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

---

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

### GTC counters always zero

**Normal behavior** - GTC error counters only increment when errors occur. Zero means healthy fiber link.

### ISP showing "Unknown"

**Cause:** GPON serial prefix not in known ISP list

**Solutions:**
1. Check GPON Serial in diagnostics
2. Open issue to add your ISP's prefix

---

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
1. Monitor the `onu_uptime` sensor in HA (HACS) or `bridge_uptime` (Docker)
2. Create HA automation to alert if `ssh_connection` goes offline
3. Check alias restoration logs periodically

---

## Performance Issues

### High CPU usage

**Cause:** Too frequent polling

**Solution:**
- HACS: Options → increase scan interval
- Docker: Increase `POLL_INTERVAL_SECONDS` (default: 60, try 120)

### Container memory growth

**Cause:** Log accumulation (rare)

**Solution:** Restart container periodically or add log rotation

---

## Getting Help

1. **HACS:** Download diagnostics (Settings → Devices & Services → 8311 ONU Monitor → device → Download diagnostics)
2. **Docker:** Check logs: `docker logs 8311-ha-bridge`
3. Enable debug mode for detailed logging
4. Open an issue with logs and configuration (scrub credentials!)
