# Homedeck
A dashboard for displaying systems, services, processes, in an organized dashboard form

## Setup
Install dependencies before running the dashboard:

```bash
python -m pip install -r requirements.txt
```

## Themes
Homedeck supports a manual theme picker with automatic hourly rotation. See
`docs/themes.md` for the full list of themes and rotation details.

## Service integrations
Service checks are configured in `nodes.yaml` and support HTTP, TCP, and local systemd
units. See `docs/services.md` for configuration details.
