import http.client
import socket
import subprocess

import collector


def test_check_http_service_ok(monkeypatch):
    class FakeResponse:
        status = 200

    class FakeConnection:
        def __init__(self, host, port, timeout=None):
            self.host = host
            self.port = port
            self.timeout = timeout

        def request(self, method, path):
            assert method == "GET"
            assert path == "/"

        def getresponse(self):
            return FakeResponse()

        def close(self):
            return None

    monkeypatch.setattr(http.client, "HTTPConnection", FakeConnection)

    result = collector.check_http_service("example.com", 80)

    assert result["status"] == "ok"
    assert result["detail"] == "HTTP 200"
    assert result["latency_ms"] is not None


def test_check_http_service_warn(monkeypatch):
    class FakeResponse:
        status = 404

    class FakeConnection:
        def __init__(self, host, port, timeout=None):
            self.host = host
            self.port = port
            self.timeout = timeout

        def request(self, method, path):
            assert method == "GET"
            assert path == "/status"

        def getresponse(self):
            return FakeResponse()

        def close(self):
            return None

    monkeypatch.setattr(http.client, "HTTPConnection", FakeConnection)

    result = collector.check_http_service("example.com", 80, path="/status")

    assert result["status"] == "warn"
    assert result["detail"] == "HTTP 404"


def test_check_tcp_service_ok(monkeypatch):
    class DummySocket:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        socket, "create_connection", lambda *args, **kwargs: DummySocket()
    )

    result = collector.check_tcp_service("127.0.0.1", 22)

    assert result["status"] == "ok"
    assert result["detail"] == "TCP OK"
    assert result["latency_ms"] is not None


def test_check_systemd_service_active(monkeypatch):
    class DummyCompleted:
        def __init__(self):
            self.stdout = "active\n"
            self.stderr = ""
            self.returncode = 0

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: DummyCompleted())

    result = collector.check_systemd_service("RSAssistant.service")

    assert result["status"] == "ok"
    assert result["detail"] == "active"


def test_check_service_missing_host_port():
    result = collector.check_service({"name": "Missing", "type": "http"}, "now")

    assert result["status"] == "unknown"
    assert result["detail"] == "Missing host/port"
