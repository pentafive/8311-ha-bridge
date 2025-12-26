# Alternative Deployments

Beyond Docker Compose, here are other ways to run 8311 HA Bridge.

## systemd Service (Bare Metal)

For running directly on a Linux host without Docker.

### Setup

```bash
# Clone and setup
cd /opt
git clone https://github.com/pentafive/8311-ha-bridge.git
cd 8311-ha-bridge
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Edit your settings
```

### Service File

Create `/etc/systemd/system/8311-ha-bridge.service`:

```ini
[Unit]
Description=8311 HA Bridge - WAS-110 to Home Assistant
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/8311-ha-bridge
Environment=PATH=/opt/8311-ha-bridge/.venv/bin:/usr/bin
EnvironmentFile=/opt/8311-ha-bridge/.env
ExecStart=/opt/8311-ha-bridge/.venv/bin/python3 8311-ha-bridge.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

### Enable and Start

```bash
systemctl daemon-reload
systemctl enable 8311-ha-bridge
systemctl start 8311-ha-bridge
systemctl status 8311-ha-bridge
```

### Logs

```bash
journalctl -u 8311-ha-bridge -f
```

## Proxmox LXC Container

Lightweight alternative to full VM.

### Create Container

1. Create Debian/Ubuntu LXC container
2. Ensure network access to WAS-110 subnet
3. Install dependencies:

```bash
apt update && apt install -y python3 python3-venv python3-pip openssh-client
```

4. Follow systemd setup above

### Network Notes

- LXC may need bridge configuration for 192.168.11.0/24 access
- Check Proxmox firewall rules

## Synology NAS (Docker)

### Via Container Manager

1. Download image or build from Dockerfile
2. Create container with environment variables
3. Map `/etc/localtime` for correct timestamps

### Via SSH

```bash
# SSH to Synology
cd /volume1/docker
git clone https://github.com/pentafive/8311-ha-bridge.git
cd 8311-ha-bridge
cp .env.example .env
nano .env

# Run with docker-compose
docker-compose up -d
```

## Home Assistant Add-on (Future)

A native HA add-on is planned for easier integration. Until then, run as a separate container.

## Kubernetes / k3s

Basic deployment manifest:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: 8311-ha-bridge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: 8311-ha-bridge
  template:
    metadata:
      labels:
        app: 8311-ha-bridge
    spec:
      containers:
      - name: 8311-ha-bridge
        image: ghcr.io/pentafive/8311-ha-bridge:latest
        env:
        - name: WAS_110_HOST
          value: "192.168.11.1"
        - name: HA_MQTT_BROKER
          valueFrom:
            secretKeyRef:
              name: 8311-secrets
              key: mqtt-broker
        - name: HA_MQTT_PASS
          valueFrom:
            secretKeyRef:
              name: 8311-secrets
              key: mqtt-password
```

**Note:** Ensure pod network can reach 192.168.11.0/24.

## Contributing

Have another deployment method working? Add it here!
