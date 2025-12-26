# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in 8311 HA Bridge, please report it responsibly:

1. **Do NOT open a public issue**
2. **Email**: pentafive@gmail.com with subject "8311-ha-bridge Security Issue"
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix timeline**: Depends on severity, typically 1-4 weeks

## Security Considerations

### Credentials

- SSH credentials for WAS-110 are stored in environment variables
- MQTT credentials are stored in environment variables
- **Never commit `.env` files** - only `.env.example` with placeholders
- Consider using Docker secrets or a secrets manager in production

### Network Security

- The bridge connects to WAS-110 via SSH (port 22)
- The bridge connects to MQTT broker (default port 1883)
- Consider using MQTT over TLS (port 8883) if your broker supports it
- Restrict network access to the bridge container

### SSH Security

- The bridge uses native SSH via subprocess
- SSH host key verification is disabled (`StrictHostKeyChecking=no`) for ease of setup
- For hardened environments, consider:
  - Pre-populating `known_hosts`
  - Using SSH key authentication instead of passwords

### Logging

- Debug mode may log sensitive information
- Keep `DEBUG_MODE=False` in production
- Review logs before sharing in issue reports

## Scope

This security policy covers:
- The `8311-ha-bridge.py` script
- Docker configuration files
- Example configurations

It does NOT cover:
- WAS-110 device security (see [8311 community](https://github.com/up-n-atom/8311))
- Home Assistant security
- MQTT broker security
