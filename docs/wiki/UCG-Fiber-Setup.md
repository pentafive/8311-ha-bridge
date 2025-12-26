# UniFi Gateway Setup for WAS-110 Monitoring

This guide covers network configuration for UniFi gateways (UCG-Fiber, UDM-Pro, UDM-SE, etc.) when running 8311-ha-bridge.

## Network Topology

```
[Docker Host] --> [UniFi Gateway] --> [WAS-110 ONU]
   (your LAN)        (SFP+ port)       192.168.11.1
```

The WAS-110 uses a separate management subnet (192.168.11.0/24) on the SFP+ port. Your gateway needs an IP on this subnet to route traffic.

## Step 1: Identify Your SFP+ Interface

**Important:** The interface name varies by gateway model and port location.

```bash
# SSH to your gateway, then:

# List all interfaces
ip link show

# Common SFP+ interface names:
# - eth6, eth7, eth8, eth9 (UCG-Fiber, UDM-Pro)
# - eth4, eth5 (UDM-SE)
# - sfp0, sfp1 (some models)

# Find interface with link to WAS-110 (shows 10Gbps or 2.5Gbps)
ethtool eth6 | grep "Link detected"
```

**Note your interface name - you'll need it below.**

## Step 2: IP Alias Configuration (CRITICAL)

### The Problem

The gateway needs an IP alias on the SFP+ interface to route traffic to 192.168.11.1. However, UniFi controller provisioning events can **silently remove** interface customizations. The `/data/on-boot.d/` scripts only run at boot, not after provisioning.

### The Solution: Cron-Based Resilience

Use a cron job that checks and restores the alias every 5 minutes.

**Execute on gateway (SSH as root):**

```bash
# Set your interface name (from Step 1)
IFACE="eth6"  # <-- CHANGE THIS to your SFP+ interface

# Create the check script
mkdir -p /data/scripts

cat > /data/scripts/check-was110-alias.sh << EOF
#!/bin/sh
# Check if $IFACE has the WAS-110 management alias
# If missing, restore it and log the event
if ! ip addr show $IFACE | grep -q "192.168.11.2"; then
    ip addr add 192.168.11.2/24 dev $IFACE 2>/dev/null
    logger -t was110-alias "Restored 192.168.11.2/24 alias to $IFACE"
fi
EOF

chmod +x /data/scripts/check-was110-alias.sh

# Add cron job (every 5 minutes)
(crontab -l 2>/dev/null | grep -v "check-was110-alias"; \
 echo "*/5 * * * * /data/scripts/check-was110-alias.sh") | crontab -

# Verify cron is set
crontab -l
```

### Immediate Fix (If Alias Missing Now)

```bash
# Replace eth6 with your interface
ip addr add 192.168.11.2/24 dev eth6
```

### Verify Connectivity

```bash
# From gateway
ping -c 3 192.168.11.1

# Check alias is present (replace eth6 with your interface)
ip addr show eth6 | grep "192.168.11"
```

## Step 3: Docker Host Routing (If Needed)

If your Docker host has IP conflicts with 192.168.11.0/24 (common with Docker bridge networks), add an explicit route.

**Test first:**
```bash
ping -c 3 192.168.11.1
```

**If unreachable, add route:**
```bash
# Replace GATEWAY_IP with your UniFi gateway's LAN IP
# Replace INTERFACE with your host's network interface
ip route add 192.168.11.1/32 via GATEWAY_IP dev INTERFACE
```

**Make persistent** (Debian/Ubuntu - add to `/etc/network/interfaces`):
```
up ip route add 192.168.11.1/32 via GATEWAY_IP dev INTERFACE
```

## Monitoring

Check logs for alias restoration events:

```bash
grep "was110-alias" /var/log/messages | tail -10
```

If you see frequent restorations, investigate what's triggering provisioning events in your UniFi controller.

## SSH Key Setup (Optional)

The WAS-110 with 8311 firmware typically allows passwordless root login. For SSH keys:

```bash
# Generate key on Docker host
ssh-keygen -t ed25519 -f ~/.ssh/was110_key -N ""

# Copy to WAS-110
ssh-copy-id -i ~/.ssh/was110_key root@192.168.11.1

# Mount in container (update docker-compose.yaml)
volumes:
  - ~/.ssh/was110_key:/root/.ssh/id_ed25519:ro
```

## Why /data/?

The `/data/` directory on UniFi gateways persists across firmware updates and reboots. Always store custom scripts here.

## Files After Setup

```
/data/
├── scripts/
│   └── check-was110-alias.sh    # Alias check script
└── on-boot.d/
    └── 20-add-was110-alias.sh   # Optional: boot-time setup (backup)
```

Cron entry: `*/5 * * * * /data/scripts/check-was110-alias.sh`
