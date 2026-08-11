"""Launcher-owned loopback HTTP boundary for C4-II Restore control.

The server is intentionally narrow: exact loopback bind, exact Host/Origin,
one-use bootstrap, explicit bearer session, state/heartbeat/select/cancel and
the B2 queue-only execute command. The HTTP worker never executes C4-I.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import threading
from typing import Callable
from urllib.parse import urlsplit

from launcher.restore.control_protocol import (
    ControlSessionError,
    SourceSelectionAdapter,
)
from launcher.restore.control_session import RestoreControlSession
from launcher.restore.validation_session import RestoreCandidatePreparationService

CONTROL_HOST = "127.0.0.1"
MAX_REQUEST_BYTES = 4096
REQUEST_ID_PATTERN = re.compile(r"[0-9a-fA-F]{32,128}\Z")

_PATH_METHODS: dict[str, tuple[str, tuple[str, ...]]] = {
    "/v1/bootstrap": ("POST", ("content-type",)),
    "/v1/state": ("GET", ("authorization",)),
    "/v1/heartbeat": ("POST", ("authorization", "content-type")),
    "/v1/restore/select": ("POST", ("authorization", "content-type")),
    "/v1/restore/cancel": ("POST", ("authorization", "content-type")),
    "/v1/restore/execute": ("POST", ("authorization", "content-type")),
}


class RestoreControlPlaneError(RuntimeError):
    """Raised when the launcher cannot establish the exact local control boundary."""


class _ControlHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False


class RestoreControlPlane:
    """Own one exact-run local Restore control server and its A1 service."""

    def __init__(
        self,
        database_path: Path,
        *,
        frontend_url: str,
        picker_adapter: SourceSelectionAdapter | None = None,
        run_id: str | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.allowed_origin = _resolve_allowed_origin(frontend_url)
        self._candidate_service = RestoreCandidatePreparationService(
            Path(database_path), run_id=run_id
        )
        session_kwargs: dict[str, object] = {"picker_adapter": picker_adapter}
        if clock is not None:
            session_kwargs["clock"] = clock
        self.session = RestoreControlSession(
            self._candidate_service,
            **session_kwargs,
        )
        self._server: _ControlHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._bound_port: int | None = None

    @property
    def run_id(self) -> str:
        return self.session.run_id

    @property
    def bootstrap_capability(self) -> str:
        """Launcher-private capability. A2 never appends it to product navigation."""

        return self.session.bootstrap_capability

    @property
    def bound_port(self) -> int:
        if self._bound_port is None:
            raise RestoreControlPlaneError("Restore control plane is not running.")
        return self._bound_port

    @property
    def control_origin(self) -> str:
        return f"http://{CONTROL_HOST}:{self.bound_port}"

    @property
    def expected_host(self) -> str:
        return f"{CONTROL_HOST}:{self.bound_port}"

    def cleanup_interrupted_validation_scratch(self) -> int:
        """Call only after launcher single-instance authority has been acquired."""

        return self._candidate_service.cleanup_interrupted_validation_scratch()

    def start(self) -> "RestoreControlPlane":
        if self._server is not None:
            return self
        try:
            server = _ControlHTTPServer((CONTROL_HOST, 0), _ControlRequestHandler)
        except OSError as exc:
            self.session.close()
            raise RestoreControlPlaneError(
                "Не удалось запустить локальный канал восстановления."
            ) from exc

        server.control_plane = self  # type: ignore[attr-defined]
        host, port = server.server_address[:2]
        if host != CONTROL_HOST or not isinstance(port, int) or port <= 0:
            server.server_close()
            self.session.close()
            raise RestoreControlPlaneError(
                "Локальный канал восстановления получил небезопасный адрес."
            )

        self._server = server
        self._bound_port = port
        thread = threading.Thread(
            target=server.serve_forever,
            kwargs={"poll_interval": 0.1},
            name="restore-control-http",
            daemon=True,
        )
        self._thread = thread
        thread.start()
        self.session.start_expiry_monitor()
        return self

    def close(self) -> None:
        server = self._server
        thread = self._thread
        self._server = None
        self._thread = None
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        self.session.close()
        self._bound_port = None

    def __enter__(self) -> "RestoreControlPlane":
        return self.start()

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        self.close()


class _ControlRequestHandler(BaseHTTPRequestHandler):
    server_version = "CWOSRestoreControl/1"
    sys_version = ""

    @property
    def plane(self) -> RestoreControlPlane:
        return self.server.control_plane  # type: ignore[attr-defined]

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        try:
            path = self._validated_path()
            self._require_host()
            self._require_origin()
            expected_method, allowed_headers = _PATH_METHODS[path]
            requested_method = self._single_header(
                "Access-Control-Request-Method",
                status=403,
                code="preflight_method_rejected",
            )
            if requested_method != expected_method:
                raise ControlSessionError(403, "preflight_method_rejected")
            request_header_values = self.headers.get_all(
                "Access-Control-Request-Headers", failobj=[]
            )
            if len(request_header_values) > 1:
                raise ControlSessionError(403, "preflight_headers_rejected")
            requested_headers = {
                item.strip().lower()
                for item in (request_header_values[0] if request_header_values else "").split(",")
                if item.strip()
            }
            if not requested_headers.issubset(set(allowed_headers)):
                raise ControlSessionError(403, "preflight_headers_rejected")
            self.send_response(204)
            self._send_common_headers(cors=True)
            self.send_header("Access-Control-Allow-Methods", expected_method)
            if allowed_headers:
                self.send_header(
                    "Access-Control-Allow-Headers",
                    ", ".join(_canonical_header_name(item) for item in allowed_headers),
                )
            self.send_header("Access-Control-Max-Age", "0")
            self.end_headers()
        except ControlSessionError as exc:
            self._write_error(exc.status, exc.code)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        self._dispatch("POST")

    def do_PUT(self) -> None:  # noqa: N802
        self._write_error(405, "method_not_allowed")

    def do_PATCH(self) -> None:  # noqa: N802
        self._write_error(405, "method_not_allowed")

    def do_DELETE(self) -> None:  # noqa: N802
        self._write_error(405, "method_not_allowed")

    def _dispatch(self, method: str) -> None:
        cors = False
        try:
            path = self._validated_path()
            self._require_host()
            self._require_origin()
            cors = True
            if self.headers.get_all("Cookie", failobj=[]):
                raise ControlSessionError(400, "cookies_not_allowed")
            expected_method, _allowed_headers = _PATH_METHODS[path]
            if method != expected_method:
                raise ControlSessionError(405, "method_not_allowed")

            if path == "/v1/bootstrap":
                payload = self._read_json_body()
                _require_exact_keys(payload, {"bootstrap_token"})
                bootstrap_token = payload.get("bootstrap_token")
                if not isinstance(bootstrap_token, str):
                    raise ControlSessionError(400, "invalid_bootstrap_request")
                session_token, state = self.plane.session.bootstrap(bootstrap_token)
                self._write_json(
                    200,
                    {
                        "ok": True,
                        "run_id": self.plane.run_id,
                        "control_origin": self.plane.control_origin,
                        "session_token": session_token,
                        "heartbeat_interval_seconds": self.plane.session.heartbeat_interval_seconds,
                        "session_expiry_seconds": self.plane.session.session_expiry_seconds,
                        "state": state.to_dict(),
                    },
                    cors=True,
                )
                return

            token = self._bearer_token()
            if path == "/v1/state":
                state = self.plane.session.get_state(token)
                self._write_json(200, {"ok": True, "state": state.to_dict()}, cors=True)
                return

            payload = self._read_json_body()
            if path == "/v1/heartbeat":
                _require_exact_keys(payload, set())
                state = self.plane.session.heartbeat(token)
                self._write_json(200, {"ok": True, "state": state.to_dict()}, cors=True)
                return

            if path == "/v1/restore/execute":
                request_id, command_seq, generation = _parse_execute_payload(payload)
                reply = self.plane.session.execute(
                    token,
                    request_id=request_id,
                    command_seq=command_seq,
                    generation=generation,
                )
            else:
                request_id, command_seq = _parse_command_payload(payload)
                if path == "/v1/restore/select":
                    reply = self.plane.session.select(
                        token,
                        request_id=request_id,
                        command_seq=command_seq,
                    )
                elif path == "/v1/restore/cancel":
                    reply = self.plane.session.cancel(
                        token,
                        request_id=request_id,
                        command_seq=command_seq,
                    )
                else:  # pragma: no cover - path is validated against the table above
                    raise ControlSessionError(404, "not_found")
            self._write_json(200, reply.to_dict(), cors=True)
        except ControlSessionError as exc:
            self._write_error(exc.status, exc.code, cors=cors)

    def _validated_path(self) -> str:
        parsed = urlsplit(self.path)
        if parsed.query or parsed.fragment or parsed.path not in _PATH_METHODS:
            raise ControlSessionError(404, "not_found")
        return parsed.path

    def _single_header(self, name: str, *, status: int, code: str) -> str:
        values = self.headers.get_all(name, failobj=[])
        if len(values) != 1:
            raise ControlSessionError(status, code)
        return values[0]

    def _require_host(self) -> None:
        host = self._single_header("Host", status=421, code="host_rejected")
        if host != self.plane.expected_host:
            raise ControlSessionError(421, "host_rejected")

    def _require_origin(self) -> None:
        origin = self._single_header("Origin", status=403, code="origin_rejected")
        if origin != self.plane.allowed_origin:
            raise ControlSessionError(403, "origin_rejected")

    def _bearer_token(self) -> str:
        value = self._single_header("Authorization", status=401, code="invalid_session")
        prefix = "Bearer "
        if not value.startswith(prefix) or len(value) <= len(prefix):
            raise ControlSessionError(401, "invalid_session")
        return value[len(prefix) :]

    def _read_json_body(self) -> dict[str, object]:
        if self.headers.get_all("Transfer-Encoding", failobj=[]):
            raise ControlSessionError(400, "invalid_body")
        content_type = self._single_header(
            "Content-Type", status=415, code="content_type_required"
        )
        if content_type.split(";", 1)[0].strip().lower() != "application/json":
            raise ControlSessionError(415, "content_type_required")
        length_values = self.headers.get_all("Content-Length", failobj=[])
        if not length_values:
            raise ControlSessionError(411, "content_length_required")
        if len(length_values) != 1:
            raise ControlSessionError(400, "invalid_body")
        try:
            length = int(length_values[0])
        except ValueError as exc:
            raise ControlSessionError(400, "invalid_body") from exc
        if length < 0 or length > MAX_REQUEST_BYTES:
            raise ControlSessionError(413, "request_too_large")
        try:
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ControlSessionError(400, "invalid_json") from exc
        if not isinstance(payload, dict):
            raise ControlSessionError(400, "invalid_json")
        return payload

    def _send_common_headers(self, *, cors: bool) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        if cors:
            self.send_header("Access-Control-Allow-Origin", self.plane.allowed_origin)
            self.send_header("Vary", "Origin")

    def _write_json(self, status: int, payload: dict[str, object], *, cors: bool) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self._send_common_headers(cors=cors)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_error(self, status: int, code: str, *, cors: bool = False) -> None:
        self._write_json(status, {"ok": False, "code": code}, cors=cors)


def _resolve_allowed_origin(frontend_url: str) -> str:
    if not isinstance(frontend_url, str) or not frontend_url:
        raise RestoreControlPlaneError("Restore control plane requires a local frontend origin.")
    parsed = urlsplit(frontend_url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise RestoreControlPlaneError(
            "Restore control plane requires frontend_url to be an exact local HTTP origin."
        ) from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname != CONTROL_HOST
        or port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        raise RestoreControlPlaneError(
            "Restore control plane requires frontend_url to be an exact local HTTP origin."
        )
    return f"http://{CONTROL_HOST}:{port}"


def _canonical_header_name(name: str) -> str:
    return "-".join(part.capitalize() for part in name.split("-"))


def _require_exact_keys(payload: dict[str, object], expected: set[str]) -> None:
    if set(payload) != expected:
        raise ControlSessionError(400, "invalid_request_schema")


def _parse_request_id_and_seq(payload: dict[str, object]) -> tuple[str, int]:
    request_id = payload.get("request_id")
    command_seq = payload.get("command_seq")
    if not isinstance(request_id, str) or REQUEST_ID_PATTERN.fullmatch(request_id) is None:
        raise ControlSessionError(400, "invalid_request_id")
    if isinstance(command_seq, bool) or not isinstance(command_seq, int) or command_seq < 1:
        raise ControlSessionError(400, "invalid_command_seq")
    return request_id, command_seq


def _parse_command_payload(payload: dict[str, object]) -> tuple[str, int]:
    _require_exact_keys(payload, {"request_id", "command_seq"})
    return _parse_request_id_and_seq(payload)


def _parse_execute_payload(payload: dict[str, object]) -> tuple[str, int, int]:
    _require_exact_keys(payload, {"request_id", "command_seq", "generation"})
    request_id, command_seq = _parse_request_id_and_seq(payload)
    generation = payload.get("generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
        raise ControlSessionError(400, "invalid_generation")
    return request_id, command_seq, generation
