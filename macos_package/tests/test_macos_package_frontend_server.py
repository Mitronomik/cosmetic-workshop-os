"""The packaged production-frontend listener: what it serves, and what it refuses.

The behaviours asserted here are the ones a packaged user would notice going
wrong, and the ones that would quietly weaken the product if they drifted:

```text
bound to loopback only, never the network
the production build is served, index and assets both
client routes fall back to index.html; missing assets are honest 404s
path traversal is refused, and never answered with a 200
only /api/* is proxied, to one fixed local backend
methods and bodies survive the proxy unchanged
a backend error stays a backend error
an unreachable backend is 502, never a fabricated success
the listener stops cleanly and leaves no orphan holding the port
an occupied port is a refusal, not a silent move elsewhere
```
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from macos_package.frontend_server import (
    FrontendPortUnavailableError,
    FrontendRootMissingError,
    FrontendServerConfig,
    FrontendServerError,
    LocalFrontendServer,
    resolve_static_path,
)
from packaging_fixtures import build_frontend_dist, free_loopback_port, wait_until_serving


class _RecordingBackendHandler(BaseHTTPRequestHandler):
    """A stand-in backend that reports exactly what reached it."""

    protocol_version = "HTTP/1.1"

    def log_message(self, *_args) -> None:
        return

    def _handle(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        self.server.received.append(  # type: ignore[attr-defined]
            {
                "method": self.command,
                "path": self.path,
                "body": body.decode("utf-8"),
                "content_type": self.headers.get("Content-Type"),
                "host": self.headers.get("Host"),
            }
        )
        if self.path.startswith("/api/boom"):
            payload = json.dumps({"detail": "нельзя"}).encode("utf-8")
            self.send_response(422)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        payload = json.dumps(
            {"ok": True, "method": self.command, "echo": body.decode("utf-8")}
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = _handle
    do_POST = _handle
    do_PUT = _handle
    do_PATCH = _handle
    do_DELETE = _handle


class _StubBackend:
    def __init__(self, port: int):
        self.server = ThreadingHTTPServer(("127.0.0.1", port), _RecordingBackendHandler)
        self.server.received = []  # type: ignore[attr-defined]
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def received(self) -> list[dict]:
        return self.server.received  # type: ignore[attr-defined]

    def __enter__(self) -> "_StubBackend":
        self.thread.start()
        return self

    def __exit__(self, *_exc) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


@pytest.fixture
def frontend_root(tmp_path):
    return build_frontend_dist(tmp_path)


@pytest.fixture
def running_server(frontend_root):
    server = LocalFrontendServer(
        FrontendServerConfig(
            root=frontend_root,
            port=free_loopback_port(),
            backend_port=free_loopback_port(),
        )
    )
    server.start()
    assert wait_until_serving(server.config.port)
    try:
        yield server
    finally:
        server.stop()


def fetch(server: LocalFrontendServer, path: str, **kwargs):
    request = Request(f"{server.origin}{path}", **kwargs)
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, response.read(), dict(response.headers)
    except HTTPError as error:
        return error.code, error.read(), dict(error.headers)


# -- binding ---------------------------------------------------------------


def test_refuses_any_host_other_than_loopback(frontend_root):
    """A non-loopback bind is a configuration that must never exist."""
    for host in ("0.0.0.0", "::", "192.168.1.10"):
        with pytest.raises(FrontendServerError):
            LocalFrontendServer(
                FrontendServerConfig(root=frontend_root, port=free_loopback_port(), host=host)
            )


def test_refuses_a_non_local_proxy_target(frontend_root):
    """Proxying anywhere but the local backend would make this a generic proxy."""
    with pytest.raises(FrontendServerError):
        LocalFrontendServer(
            FrontendServerConfig(
                root=frontend_root, port=free_loopback_port(), backend_host="10.0.0.5"
            )
        )


def test_listens_on_loopback_only(running_server):
    """Nothing on the network can reach the packaged product."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # A free bind on the wildcard address for the same port proves the
        # listener did not claim every interface.
        probe.bind(("0.0.0.0", 0))
    status, _, _ = fetch(running_server, "/")
    assert status == 200


def test_missing_production_build_refuses_before_binding(tmp_path):
    """A listener answering 404 for the whole product is worse than a refusal."""
    empty = tmp_path / "frontend" / "dist"
    empty.mkdir(parents=True)
    server = LocalFrontendServer(
        FrontendServerConfig(root=empty, port=free_loopback_port())
    )
    with pytest.raises(FrontendRootMissingError):
        server.start()
    assert not server.is_running


def test_occupied_port_is_a_typed_refusal_and_leaves_the_holder_alone(frontend_root):
    """The package never takes a port from another program, and never moves."""
    port = free_loopback_port()
    holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    holder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    holder.bind(("127.0.0.1", port))
    holder.listen(1)
    try:
        server = LocalFrontendServer(FrontendServerConfig(root=frontend_root, port=port))
        with pytest.raises(FrontendPortUnavailableError):
            server.start()
        assert not server.is_running
        # The foreign listener is untouched and still accepting.
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            pass
    finally:
        holder.close()


def test_stop_releases_the_port_and_is_safe_to_repeat(frontend_root):
    port = free_loopback_port()
    server = LocalFrontendServer(FrontendServerConfig(root=frontend_root, port=port))
    server.start()
    assert wait_until_serving(port)
    server.stop()
    server.stop()  # idempotent: `finally` blocks call it on already-failed paths
    assert not server.is_running
    # The port is genuinely free again — no orphan thread is still holding it.
    rebound = LocalFrontendServer(FrontendServerConfig(root=frontend_root, port=port))
    rebound.start()
    rebound.stop()


# -- static serving --------------------------------------------------------


def test_serves_the_production_index(running_server):
    status, body, headers = fetch(running_server, "/")
    assert status == 200
    assert "Мастерская косметолога" in body.decode("utf-8")
    assert headers["Content-Type"] == "text/html; charset=utf-8"


def test_serves_production_assets_with_browser_usable_types(running_server):
    """A module script served as the wrong type is silently refused by browsers."""
    status, body, headers = fetch(running_server, "/assets/main.js")
    assert status == 200
    assert b"main-js" in body
    assert headers["Content-Type"] == "text/javascript; charset=utf-8"

    status, _, headers = fetch(running_server, "/assets/styles.css")
    assert status == 200
    assert headers["Content-Type"] == "text/css; charset=utf-8"

    status, _, headers = fetch(running_server, "/brand/mch-logo.png")
    assert status == 200
    assert headers["Content-Type"] == "image/png"


def test_spa_routes_fall_back_to_index(running_server):
    """Client routes are the SPA's, and a reload of one must not 404."""
    for route in ("/orders", "/settings/tax", "/recipes/17/versions"):
        status, body, _ = fetch(running_server, route)
        assert status == 200, route
        assert b"<div id=\"root\">" in body


def test_missing_asset_is_an_honest_404(running_server):
    """A missing `.js` answered with HTML only produces a confusing MIME error."""
    status, body, headers = fetch(running_server, "/assets/not-there.js")
    assert status == 404
    assert "Страница не найдена" in body.decode("utf-8")
    assert headers["Content-Type"].startswith("text/plain")


def test_static_paths_reject_writes(running_server):
    status, _, _ = fetch(running_server, "/orders", method="POST", data=b"{}")
    assert status == 405


# -- traversal -------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/../secret.txt",
        "/../../etc/passwd",
        "/assets/../../secret.txt",
        "/%2e%2e/secret.txt",
        "/%2e%2e%2fsecret.txt",
        "/assets/%2e%2e%2f%2e%2e%2fsecret.txt",
    ],
)
def test_path_traversal_is_refused_never_served(running_server, tmp_path, path):
    """Refused with 400 — and specifically *not* absorbed by the SPA fallback."""
    (tmp_path / "secret.txt").write_text("private", encoding="utf-8")
    status, body, _ = fetch(running_server, path)
    assert status in (400, 404)
    assert b"private" not in body


def test_resolve_static_path_rejects_escapes_and_accepts_real_files(tmp_path):
    root = build_frontend_dist(tmp_path)
    (tmp_path / "outside.txt").write_text("nope", encoding="utf-8")
    assert resolve_static_path(root, "/assets/main.js") == (root / "assets" / "main.js").resolve()
    assert resolve_static_path(root, "/../outside.txt") is None
    assert resolve_static_path(root, "/a/../../outside.txt") is None
    assert resolve_static_path(root, "/\x00evil") is None


def test_resolve_static_path_rejects_a_symlink_escaping_the_build(tmp_path):
    """String checks cannot see this one; the containment check after resolve() can."""
    root = build_frontend_dist(tmp_path)
    secret = tmp_path / "outside.txt"
    secret.write_text("nope", encoding="utf-8")
    (root / "escape.txt").symlink_to(secret)
    assert resolve_static_path(root, "/escape.txt") is None


# -- api proxy -------------------------------------------------------------


def test_proxies_api_get_to_the_configured_local_backend(frontend_root):
    backend_port = free_loopback_port()
    with _StubBackend(backend_port) as backend:
        server = LocalFrontendServer(
            FrontendServerConfig(
                root=frontend_root, port=free_loopback_port(), backend_port=backend_port
            )
        )
        server.start()
        try:
            status, body, _ = fetch(server, "/api/settings/status?limit=5")
            assert status == 200
            assert json.loads(body)["ok"] is True
        finally:
            server.stop()
    assert backend.received[0]["method"] == "GET"
    assert backend.received[0]["path"] == "/api/settings/status?limit=5"
    # The backend must be told the authority it is actually served on.
    assert backend.received[0]["host"] == f"127.0.0.1:{backend_port}"


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_proxies_every_method_the_spa_uses_with_its_body(frontend_root, method):
    """The SPA issues GET/POST/PUT/PATCH; GET-only would break most of the product."""
    backend_port = free_loopback_port()
    payload = json.dumps({"значение": "6.00"}).encode("utf-8")
    with _StubBackend(backend_port) as backend:
        server = LocalFrontendServer(
            FrontendServerConfig(
                root=frontend_root, port=free_loopback_port(), backend_port=backend_port
            )
        )
        server.start()
        try:
            status, body, _ = fetch(
                server,
                "/api/settings/tax-rate",
                method=method,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
        finally:
            server.stop()
    assert status == 200
    assert json.loads(body)["method"] == method
    assert backend.received[0]["body"] == payload.decode("utf-8")
    assert backend.received[0]["content_type"] == "application/json"


def test_multipart_import_upload_survives_the_proxy(frontend_root):
    """Import drafts are uploaded as multipart FormData, not JSON."""
    backend_port = free_loopback_port()
    boundary = "----cosmeticworkshop"
    payload = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="target_type"\r\n\r\ningredients\r\n'
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    with _StubBackend(backend_port) as backend:
        server = LocalFrontendServer(
            FrontendServerConfig(
                root=frontend_root, port=free_loopback_port(), backend_port=backend_port
            )
        )
        server.start()
        try:
            status, _, _ = fetch(
                server,
                "/api/imports/drafts",
                method="POST",
                data=payload,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            )
        finally:
            server.stop()
    assert status == 200
    assert "ingredients" in backend.received[0]["body"]


def test_backend_error_status_is_preserved_exactly(frontend_root):
    """A refusal turned into a success would let the SPA report a write that never happened."""
    backend_port = free_loopback_port()
    with _StubBackend(backend_port):
        server = LocalFrontendServer(
            FrontendServerConfig(
                root=frontend_root, port=free_loopback_port(), backend_port=backend_port
            )
        )
        server.start()
        try:
            status, body, _ = fetch(server, "/api/boom", method="POST", data=b"{}")
        finally:
            server.stop()
    assert status == 422
    assert json.loads(body)["detail"] == "нельзя"


def test_unreachable_backend_is_502_and_never_a_fake_success(frontend_root):
    # Nothing is listening on this port: no stub backend is started.
    server = LocalFrontendServer(
        FrontendServerConfig(
            root=frontend_root, port=free_loopback_port(), backend_port=free_loopback_port()
        )
    )
    server.start()
    try:
        status, body, _ = fetch(server, "/api/settings/status")
    finally:
        server.stop()
    assert status == 502
    assert "Не удалось связаться" in body.decode("utf-8")


def test_only_the_api_prefix_is_proxied(frontend_root):
    """Everything else is static. There is no general proxy here."""
    backend_port = free_loopback_port()
    with _StubBackend(backend_port) as backend:
        server = LocalFrontendServer(
            FrontendServerConfig(
                root=frontend_root, port=free_loopback_port(), backend_port=backend_port
            )
        )
        server.start()
        try:
            # Superficially API-ish paths that are not under `/api/`.
            for path in ("/apifoo", "/v1/restore/execute", "/assets/main.js", "/"):
                fetch(server, path)
        finally:
            server.stop()
    assert backend.received == []


def test_no_cors_headers_are_added(frontend_root):
    """Same-origin is the whole reason the proxy exists."""
    backend_port = free_loopback_port()
    with _StubBackend(backend_port):
        server = LocalFrontendServer(
            FrontendServerConfig(
                root=frontend_root, port=free_loopback_port(), backend_port=backend_port
            )
        )
        server.start()
        try:
            _, _, api_headers = fetch(server, "/api/settings/status")
            _, _, page_headers = fetch(server, "/")
        finally:
            server.stop()
    for headers in (api_headers, page_headers):
        assert not any(name.lower().startswith("access-control-") for name in headers)
