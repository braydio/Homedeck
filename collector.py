import subprocess
import time
import yaml
from datetime import datetime, timezone

PING_COUNT = 1
PING_TIMEOUT = 1  # seconds


def ping(host: str) -> float | None:
    """
    Returns latency in ms if reachable, else None.
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


def load_nodes(path="nodes.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)["nodes"]


def collect():
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
                "latency_ms": round(latency, 1) if latency else None,
                "last_seen": last_seen,
            }
        )

    return {
        "generated_at": now,
        "nodes": results,
    }

