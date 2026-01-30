# Service integrations

Homedeck can check HTTP, TCP, and local systemd services. Service checks are defined in
`nodes.yaml` under the `services` key.

## Example configuration

```yaml
services:
  - name: Jellyfin
    type: http
    host: 192.168.1.198
    port: 8097
    path: /

  - name: RSAssistant
    type: systemd
    unit: RSAssistant.service

  - name: SSH
    type: tcp
    host: 192.168.1.198
    port: 22
```

## Fields

- `name` (required): Human-friendly label.
- `type` (optional): `http`, `https`, `tcp`, or `systemd`. Defaults to `http`.
- `host` (required for `http`, `https`, `tcp`): Hostname or IP.
- `port` (required for `http`, `https`, `tcp`): Port number.
- `path` (optional for `http`, `https`): HTTP path to request. Defaults to `/`.
- `unit` (required for `systemd`): Systemd unit name checked locally via `systemctl is-active`.

## Notes

- HTTP services classify `200-399` as OK, `400-499` as WARN, and `500+` as DOWN.
- Systemd checks run locally. To monitor remote systemd services, use a remote exporter
  and define it as an HTTP/TCP service instead.
