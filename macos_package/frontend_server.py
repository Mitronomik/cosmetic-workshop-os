"""Serve the production frontend build locally, with no Node at runtime.

Development serves the SPA through `frontend/scripts/dev-server.mjs`, which
needs Node. The packaged user must not need Node, so the packaged product needs
its own way to put the already-built `frontend/dist` on the exact origin the
product expects. This is that, written against the Python standard library only.

It is deliberately narrow, and each narrowing is load-bearing:

```text
binds 127.0.0.1 only          never reachable from the network
serves one fixed root         frontend/dist and nothing else on disk
SPA fallback to index.html    extensionless routes are client routes
proxies only /api/*           one prefix, one fixed localhost backend
adds no CORS headers          same-origin is the whole point
holds no business logic       the backend stays the API authority
```

## Why a proxy at all

The SPA calls same-origin paths — `fetch('/api/settings/status')`. Serving the
page from one origin and the API from another would turn every one of those into
a cross-origin request, which would mean either rewriting the frontend (a closed
boundary) or opening CORS (a security regression for a local product). Proxying
one prefix keeps the browser seeing exactly the same single origin it sees in
development, so nothing about the SPA or the backend has to change.

This is **not** a general proxy. The target is a fixed loopback host and port
supplied by the packaged entrypoint; no request can influence where a proxied
request goes, and no path outside `/api/` is proxied at all.

## Why the errors are shaped the way they are

A backend that answers `422` or `500` must reach the browser as `422` or `500`.
Turning a backend refusal into anything friendlier here would make the frontend
believe a write succeeded when it did not — for a product whose whole point is
inventory and production truth, that is the worst possible failure mode. The
only status this module invents is `502`, for the case where the backend could
not be reached at all, and that is unambiguous.

## What owns its lifetime

The packaged entrypoint starts it and stops it. Its threads are daemons and its
socket is closed on `stop()`, so it cannot outlive the launcher as an orphan
holding the frontend port.
"""

from __future__ import annotations

from dataclasses import dataclass
import errno
from http.client import HTTPConnection, HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path, PurePosixPath
import socket
import threading
from urllib.parse import unquote, urlsplit

LOOPBACK_HOST = "127.0.0.1"

# The origin the launcher already configures as the local frontend, and which
# ADR 0018 requires the Restore control plane to accept as an exact Origin. The
# packaged product keeps it rather than choosing a new one, so the control-plane
# Origin/Host checks, the bootstrap fragment handoff and reload semantics all
# stay exactly as they were verified.
DEFAULT_FRONTEND_PORT = 5173

DEFAULT_BACKEND_PORT = 8000

# The one proxied prefix. Everything else is a static file or an SPA route.
API_PATH_PREFIX = "/api/"

# Long enough for an import apply or a production confirmation on a slow
# machine; bounded so a wedged backend cannot pin a worker thread forever.
BACKEND_TIMEOUT_SECONDS = 300.0

# Per-connection hop-by-hop headers. Forwarding them would let one connection's
# framing decisions leak into the other connection and corrupt the response.
HOP_BY_HOP_HEADERS = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
)

# What the SPA actually issues. Kept as an allowlist rather than "whatever
# arrives", so the proxy surface stays a reviewable list.
PROXIED_METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"})

STREAM_CHUNK_BYTES = 64 * 1024

# `mimetypes` disagrees with browsers about JavaScript on some systems, and a
# module script served as `application/javascript` or worse is silently refused
# by the browser. Pinned here so the packaged product cannot depend on the
# machine's `/etc/mime.types`.
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".map": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
}

NOT_FOUND_BODY = "Страница не найдена".encode("utf-8")
BAD_REQUEST_BODY = "Некорректный адрес".encode("utf-8")
METHOD_NOT_ALLOWED_BODY = "Действие не поддерживается".encode("utf-8")
BACKEND_UNREACHABLE_BODY = (
    "Не удалось связаться с локальной рабочей частью приложения. "
    "Закройте приложение и откройте его снова."
).encode("utf-8")


class FrontendServerError(RuntimeError):
    """The packaged frontend listener cannot start safely."""


class FrontendRootMissingError(FrontendServerError):
    """The production frontend build is not where the package says it is."""


class FrontendPortUnavailableError(FrontendServerError):
    """The configured frontend port is held by something else, right now.

    A distinct type because the response to it is distinct: the packaged product
    refuses and tells the user to close the other program. It never takes the
    port from whoever has it, and it never quietly moves to a different port —
    a different port would break the exact Origin the Restore control plane
    checks, so "somewhere else" is not a safe recovery.
    """


@dataclass(frozen=True)
class FrontendServerConfig:
    """Everything the listener is allowed to decide, decided once, up front."""

    root: Path
    port: int = DEFAULT_FRONTEND_PORT
    backend_host: str = LOOPBACK_HOST
    backend_port: int = DEFAULT_BACKEND_PORT
    host: str = LOOPBACK_HOST

    @property
    def origin(self) -> str:
        return f"http://{self.host}:{self.port}"


def validate_frontend_server_config(config: FrontendServerConfig) -> FrontendServerConfig:
    """Refuse anything that would widen the listener beyond loopback.

    Both host checks are here rather than at the bind, because a non-loopback
    bind is not a runtime accident to recover from — it is a configuration that
    must never have existed. The same applies to the proxy target: a packaged
    product that could be pointed at a remote backend would be a generic proxy,
    which is exactly what this must not become.
    """
    if config.host != LOOPBACK_HOST:
        raise FrontendServerError(
            "The packaged frontend server must listen on 127.0.0.1 only."
        )
    if config.backend_host != LOOPBACK_HOST:
        raise FrontendServerError(
            "The packaged frontend server may only proxy to the local backend on 127.0.0.1."
        )
    for port in (config.port, config.backend_port):
        if not 1 <= port <= 65535:
            raise FrontendServerError(f"Port {port!r} is invalid. Use a port from 1 to 65535.")
    return config


def resolve_static_path(root: Path, url_path: str) -> Path | None:
    """Map a URL path to a file inside `root`, or refuse.

    `None` means "this request may not be answered from disk at all" — it is not
    the same as "no such file", and the caller must not fall back to the SPA
    index for it. Refused: any `..` segment, a NUL byte, and anything that
    resolves outside the root.

    `..` is rejected outright rather than normalized away. Normalizing is the
    usual approach and the usual bug: it makes the safety of the result depend
    on getting decode order, separators and encodings all correct, and
    `%2e%2e%2f` variants exist precisely to break that. Rejecting the segment is
    a decision no encoding can talk its way past.

    The containment check after `resolve()` is a second, independent barrier. It
    is what catches a symlink *inside* the packaged build pointing outward —
    a case no amount of string inspection can see.
    """
    decoded = unquote(urlsplit(url_path).path)
    if "\x00" in decoded:
        return None
    parts = [part for part in PurePosixPath(decoded).parts if part not in ("", "/", ".")]
    if any(part == ".." for part in parts):
        return None
    # Windows-style separators cannot appear in a POSIX path segment, but a
    # crafted request can put one *inside* one. Refuse rather than interpret.
    if any("\\" in part for part in parts):
        return None
    root_resolved = root.resolve()
    candidate = root_resolved.joinpath(*parts) if parts else root_resolved
    try:
        resolved = candidate.resolve()
    except (OSError, RuntimeError):
        return None
    if resolved != root_resolved and root_resolved not in resolved.parents:
        return None
    return resolved


def content_type_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in CONTENT_TYPES:
        return CONTENT_TYPES[suffix]
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


class _FrontendHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler, *, config: FrontendServerConfig):
        self.config = config
        self.frontend_root = config.root.resolve()
        super().__init__(address, handler)


class _FrontendRequestHandler(BaseHTTPRequestHandler):
    # HTTP/1.1 so the browser may keep the connection alive for the asset
    # requests that immediately follow index.html.
    protocol_version = "HTTP/1.1"
    server_version = "CosmeticWorkshopLocal/1.0"
    sys_version = ""

    # The packaged product has no console anyone reads, and a per-request access
    # log in a user's Console is noise. Errors still surface where they matter:
    # as HTTP statuses to the SPA.
    def log_message(self, format: str, *args) -> None:  # noqa: A002 - stdlib signature
        return

    @property
    def config(self) -> FrontendServerConfig:
        return self.server.config  # type: ignore[attr-defined]

    def do_GET(self) -> None:  # noqa: N802 - stdlib naming
        self._dispatch("GET")

    def do_HEAD(self) -> None:  # noqa: N802
        self._dispatch("HEAD")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def do_PUT(self) -> None:  # noqa: N802
        self._dispatch("PUT")

    def do_PATCH(self) -> None:  # noqa: N802
        self._dispatch("PATCH")

    def do_DELETE(self) -> None:  # noqa: N802
        self._dispatch("DELETE")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._dispatch("OPTIONS")

    def _dispatch(self, method: str) -> None:
        # One handler instance serves every request on a keep-alive connection,
        # so any per-response state has to be cleared here rather than trusted
        # to be fresh. `_headers_flushed` is the one that matters: left over
        # `True` from a previous successful request, a later backend failure
        # would look like "headers already sent for *this* response" and the
        # connection would be dropped instead of returning the honest 502.
        self._begin_response()
        path = urlsplit(self.path).path
        if path.startswith(API_PATH_PREFIX):
            self._proxy_to_backend(method)
            return
        if method not in ("GET", "HEAD"):
            # Static content is read-only. A write aimed at a non-API path is a
            # bug or a probe, and either way it is not something to guess about.
            self._respond_bytes(
                405, "text/plain; charset=utf-8", METHOD_NOT_ALLOWED_BODY, method, close=True
            )
            return
        self._serve_static(method)

    # -- static -----------------------------------------------------------

    def _serve_static(self, method: str) -> None:
        url_path = urlsplit(self.path).path
        resolved = resolve_static_path(self.server.frontend_root, url_path)  # type: ignore[attr-defined]
        if resolved is None:
            # Refused, not missing. Never falls through to the SPA index: a
            # traversal attempt must not be answered with a 200.
            self._respond_bytes(
                400, "text/plain; charset=utf-8", BAD_REQUEST_BODY, method, close=True
            )
            return
        if resolved.is_dir():
            resolved = resolved / "index.html"
        if resolved.is_file():
            self._send_file(resolved, method)
            return
        # An extensionless path is a client-side route — the SPA owns it and the
        # index bootstraps it. A path that asked for `.js` or `.png` and is not
        # there is a genuine 404, and answering it with HTML would only produce a
        # confusing MIME error in the browser console instead.
        if not PurePosixPath(urlsplit(self.path).path).suffix:
            index = self.server.frontend_root / "index.html"  # type: ignore[attr-defined]
            if index.is_file():
                self._send_file(index, method)
                return
        self._respond_bytes(404, "text/plain; charset=utf-8", NOT_FOUND_BODY, method)

    def _send_file(self, path: Path, method: str) -> None:
        try:
            payload = path.read_bytes()
        except OSError:
            self._respond_bytes(404, "text/plain; charset=utf-8", NOT_FOUND_BODY, method)
            return
        self._respond_bytes(200, content_type_for(path), payload, method)

    def _respond_bytes(
        self,
        status: int,
        content_type: str,
        body: bytes,
        method: str,
        *,
        close: bool = False,
    ) -> None:
        """Write one complete, correctly framed response.

        `close` is set by the refusal paths that answer **without** having read
        the request body. Any unread body would still be sitting in the socket
        when the next request was parsed off it, so the connection is ended
        rather than left desynchronised.
        """
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if close:
            self.send_header("Connection", "close")
            self.close_connection = True
        self.end_headers()
        if method != "HEAD":
            self.wfile.write(body)

    # -- api proxy --------------------------------------------------------

    def _proxy_to_backend(self, method: str) -> None:
        if method not in PROXIED_METHODS:
            self._respond_bytes(
                405, "text/plain; charset=utf-8", METHOD_NOT_ALLOWED_BODY, method, close=True
            )
            return
        try:
            body = self._read_request_body()
        except (OSError, ValueError):
            self._respond_bytes(
                400, "text/plain; charset=utf-8", BAD_REQUEST_BODY, method, close=True
            )
            return

        target_host = self.config.backend_host
        target_port = self.config.backend_port
        headers = self._forwarded_request_headers(f"{target_host}:{target_port}", body)

        connection = HTTPConnection(target_host, target_port, timeout=BACKEND_TIMEOUT_SECONDS)
        try:
            connection.request(method, self.path, body=body, headers=headers)
            response = connection.getresponse()
            self._relay_response(response, method)
        except (OSError, HTTPException):
            # The backend could not be reached or died mid-response. This is the
            # only status this module invents, and it is deliberately an error:
            # a synthesized success here would let the SPA report a write that
            # never happened.
            self._respond_unreachable(method)
        finally:
            connection.close()

    def _read_request_body(self) -> bytes | None:
        if self.headers.get("Transfer-Encoding", "").lower() == "chunked":
            return self._read_chunked_body()
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            return None
        length = int(raw_length)
        if length < 0:
            raise ValueError("negative Content-Length")
        return self.rfile.read(length) if length else b""

    def _read_chunked_body(self) -> bytes:
        """Decode a chunked body so it can be forwarded with a real length.

        Browsers send `Content-Length` for both JSON and `FormData`, so this is
        a defensive path rather than the normal one — but decoding it here means
        an unusual client cannot make the proxy forward a body it never framed.
        """
        chunks = bytearray()
        while True:
            line = self.rfile.readline(65536).strip()
            size = int(line.split(b";", 1)[0] or b"0", 16)
            if size == 0:
                # Consume the trailer section up to the terminating blank line.
                while True:
                    trailer = self.rfile.readline(65536)
                    if trailer in (b"\r\n", b"\n", b""):
                        break
                return bytes(chunks)
            chunks.extend(self.rfile.read(size))
            self.rfile.read(2)

    def _forwarded_request_headers(self, target_authority: str, body: bytes | None) -> dict:
        headers: dict[str, str] = {}
        for name, value in self.headers.items():
            if name.lower() in HOP_BY_HOP_HEADERS or name.lower() == "host":
                continue
            headers[name] = value
        # The backend must see the origin it is actually served on. Passing the
        # frontend authority through would misdescribe the request to FastAPI's
        # URL generation for no benefit.
        headers["Host"] = target_authority
        if body is None:
            headers.pop("Content-Length", None)
        else:
            headers["Content-Length"] = str(len(body))
        return headers

    def _relay_response(self, response, method: str) -> None:
        """Pass the backend's own answer through, status and all.

        Body length is resolved before any header is written, so the framing this
        connection promises always matches the bytes that follow. When the
        backend gave no length — a streamed response — the connection is closed
        after the body rather than guessing a length or buffering an unbounded
        download in memory.
        """
        raw_length = response.getheader("Content-Length")
        self.send_response(response.status)
        for name, value in response.getheaders():
            if name.lower() in HOP_BY_HOP_HEADERS or name.lower() == "content-length":
                continue
            self.send_header(name, value)
        if raw_length is not None:
            self.send_header("Content-Length", raw_length)
        else:
            self.send_header("Connection", "close")
            self.close_connection = True
        self.end_headers()
        if method == "HEAD":
            return
        while True:
            chunk = response.read(STREAM_CHUNK_BYTES)
            if not chunk:
                break
            self.wfile.write(chunk)

    def _respond_unreachable(self, method: str) -> None:
        if self.headers_flushed:
            # The backend died after its headers were already on the wire.
            # Nothing truthful can be added to a response in flight, so the
            # connection is dropped and the browser reports a network failure —
            # which is what actually happened.
            self.close_connection = True
            return
        self._respond_bytes(
            502, "text/plain; charset=utf-8", BACKEND_UNREACHABLE_BODY, method
        )

    def _begin_response(self) -> None:
        """Start a new response on this connection with no inherited state."""
        self.__dict__["_headers_flushed"] = False

    @property
    def headers_flushed(self) -> bool:
        """Whether **this** request's response headers are already on the wire.

        Request-scoped by construction: reset at the top of every dispatch, set
        by :meth:`end_headers`. It answers "can I still choose a status code?",
        which is only meaningful about the response currently being written.
        """
        return bool(self.__dict__.get("_headers_flushed"))

    def end_headers(self) -> None:
        self.__dict__["_headers_flushed"] = True
        super().end_headers()


class LocalFrontendServer:
    """Own the packaged frontend listener for exactly one launcher run."""

    def __init__(self, config: FrontendServerConfig):
        self.config = validate_frontend_server_config(config)
        self._server: _FrontendHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def origin(self) -> str:
        return self.config.origin

    @property
    def is_running(self) -> bool:
        return self._server is not None

    def start(self) -> "LocalFrontendServer":
        """Bind, or refuse with the reason the caller has to tell apart.

        The root is proved before the socket is touched: binding first and then
        discovering there is nothing to serve would leave a listener answering
        404 for the whole product.
        """
        if self._server is not None:
            raise FrontendServerError("The packaged frontend server is already running.")
        root = self.config.root
        if not (root / "index.html").is_file():
            raise FrontendRootMissingError(
                "The packaged production frontend build is missing its index.html."
            )
        try:
            server = _FrontendHTTPServer(
                (self.config.host, self.config.port),
                _FrontendRequestHandler,
                config=self.config,
            )
        except OSError as exc:
            if exc.errno in (errno.EADDRINUSE, errno.EACCES):
                raise FrontendPortUnavailableError(
                    f"Порт {self.config.port} уже занят. "
                    "Закройте другое окно приложения или выберите свободный порт."
                ) from exc
            raise FrontendServerError(
                "Не удалось открыть локальный порт для окна приложения."
            ) from exc
        thread = threading.Thread(
            target=server.serve_forever,
            kwargs={"poll_interval": 0.2},
            name="cosmetic-workshop-frontend",
            daemon=True,
        )
        thread.start()
        self._server = server
        self._thread = thread
        return self

    def stop(self) -> None:
        """Release the port and the threads, and be safe to call twice.

        Called from a `finally` on every exit path — including the ones that
        already failed — so it must never raise and must never depend on having
        started successfully.
        """
        server, thread = self._server, self._thread
        self._server, self._thread = None, None
        if server is None:
            return
        try:
            server.shutdown()
        except Exception:  # noqa: BLE001 - shutdown must not mask the real failure
            pass
        try:
            server.server_close()
        except Exception:  # noqa: BLE001
            pass
        if thread is not None:
            thread.join(timeout=5.0)

    def __enter__(self) -> "LocalFrontendServer":
        return self.start()

    def __exit__(self, *_exc_info) -> None:
        self.stop()


def port_is_available(host: str, port: int) -> bool:
    """Probe a loopback port without reserving it.

    Used by tests and by nothing on the production path: the authoritative
    answer is the listener's own `bind()` in :meth:`LocalFrontendServer.start`.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def default_frontend_root(application_root: Path) -> Path:
    return application_root / "frontend" / "dist"
