import http.client
import socket
import subprocess
import time
from datetime import datetime, timezone

import yaml

PING_COUNT = 1
PING_TIMEOUT = 1  # seconds
SERVICE_TIMEOUT = 2  # seconds


def ping(host: str) -> float | None:
    """
    Ping a host once to capture latency.

    Args:
        host: Hostname or IP address to ping.

    Returns:
        Latency in milliseconds if reachable, otherwise None.
    """
    try:
        start = time.time()
        subprocess.check_output(
            ["ping", "-c", str(PING_COUNT), "-W", str(PING_TIMEOUT), host],
            stderr=subprocess.DEVNULL,
        )
        return (time.time() - start) * 1000
    except subprocess.CalledProcessError:
        return None


def load_config(path: str = "nodes.yaml") -> dict:
    """
    Load the Homedeck configuration from YAML.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        Parsed configuration dictionary.
    """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_nodes(path: str = "nodes.yaml") -> list[dict]:
    """
    Load node definitions from the configuration.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        List of node dictionaries.
    """
    config = load_config(path)
    return config.get("nodes", [])


def load_services(path: str = "nodes.yaml") -> list[dict]:
    """
    Load service definitions from the configuration.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        List of service dictionaries.
    """
    config = load_config(path)
    return config.get("services", [])


def check_http_service(
    host: str, port: int, path: str = "/", use_https: bool = False
) -> dict:
    """
    Check an HTTP(S) endpoint for availability.

    Args:
        host: Hostname or IP address.
        port: Service port number.
        path: HTTP path to request.
        use_https: Whether to use HTTPS.

    Returns:
        Dict with status, latency_ms, and detail.
    """
    start = time.time()
    connection = None
    try:
        connection_class = (
            http.client.HTTPSConnection if use_https else http.client.HTTPConnection
        )
        connection = connection_class(host, port, timeout=SERVICE_TIMEOUT)
        connection.request("GET", path)
        response = connection.getresponse()
        latency_ms = (time.time() - start) * 1000
        detail = f"HTTP {response.status}"
        if 200 <= response.status < 400:
            status = "ok"
        elif 400 <= response.status < 500:
            status = "warn"
        else:
            status = "bad"
        return {"status": status, "latency_ms": round(latency_ms, 1), "detail": detail}
    except (OSError, http.client.HTTPException) as exc:
        return {"status": "bad", "latency_ms": None, "detail": str(exc)}
    finally:
        if connection:
            connection.close()


def check_tcp_service(host: str, port: int) -> dict:
    """
    Check a TCP port for basic reachability.

    Args:
        host: Hostname or IP address.
        port: TCP port number.

    Returns:
        Dict with status, latency_ms, and detail.
    """
    start = time.time()
    try:
        with socket.create_connection((host, port), timeout=SERVICE_TIMEOUT):
            latency_ms = (time.time() - start) * 1000
            return {
                "status": "ok",
                "latency_ms": round(latency_ms, 1),
                "detail": "TCP OK",
            }
    except OSError as exc:
        return {"status": "bad", "latency_ms": None, "detail": str(exc)}


def check_systemd_service(unit: str) -> dict:
    """
    Check a local systemd unit status.

    Args:
        unit: Systemd unit name.

    Returns:
        Dict with status, latency_ms, and detail.
    """
    result = subprocess.run(
        ["systemctl", "is-active", unit],
        capture_output=True,
        text=True,
        check=False,
    )
    state = result.stdout.strip() or result.stderr.strip() or "unknown"
    if state == "active":
        status = "ok"
    elif state in {"activating", "reloading", "deactivating"}:
        status = "warn"
    else:
        status = "bad"
    return {"status": status, "latency_ms": None, "detail": state}


def check_service(service: dict, now: str) -> dict:
    """
    Evaluate a service definition for reachability.

    Args:
        service: Service configuration dictionary.
        now: ISO timestamp string for the check time.

    Returns:
        Normalized service result dictionary.
    """
    name = service.get("name") or "Unnamed service"
    service_type = (service.get("type") or "http").lower()
    host = service.get("host")
    port = service.get("port")
    path = service.get("path") or "/"
    unit = service.get("unit")

    if service_type in {"http", "https"}:
        if not host or not port:
            result = {
                "status": "unknown",
                "latency_ms": None,
                "detail": "Missing host/port",
            }
        else:
            result = check_http_service(host, int(port), path, service_type == "https")
    elif service_type == "tcp":
        if not host or not port:
            result = {
                "status": "unknown",
                "latency_ms": None,
                "detail": "Missing host/port",
            }
        else:
            result = check_tcp_service(host, int(port))
    elif service_type == "systemd":
        if not unit:
            result = {"status": "unknown", "latency_ms": None, "detail": "Missing unit"}
        else:
            result = check_systemd_service(unit)
    else:
        result = {"status": "unknown", "latency_ms": None, "detail": "Unknown type"}

    return {
        "name": name,
        "type": service_type,
        "host": host,
        "port": port,
        "status": result["status"],
        "latency_ms": result["latency_ms"],
        "detail": result["detail"],
        "checked_at": now,
    }


def collect():
    """
    Collect node and service health data.

    Returns:
        Dictionary with timestamped node and service results.
    """
    now = datetime.now(timezone.utc).isoformat()
    results = []

    for node in load_nodes():
        latency = ping(node["host"])

        if latency is None:
            status = "bad"
            last_seen = None
        else:
            status = "ok"
            last_seen = now

        results.append(
            {
                "name": node["name"],
                "role": node["role"],
                "os": node["os"],
                "status": status,
                "latency_ms": round(latency, 1) if latency is not None else None,
                "last_seen": last_seen,
            }
        )

    service_results = [check_service(service, now) for service in load_services()]

    return {
        "generated_at": now,
        "nodes": results,
        "services": service_results,
    }
