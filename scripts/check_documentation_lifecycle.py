#!/usr/bin/env python3
"""Guard C4-II-A4 browser-session implementation and closed Restore boundaries."""

from __future__ import annotations

import ast
from hashlib import sha1
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
P = lambda value: ROOT / value

README = P("README.md")
CURRENT = P("docs/current-lifecycle.md")
SLICES = P("docs/c4-ii-a-implementation-slices.md")
PROFILE = P("docs/restore-interaction-and-validation-session.md")
PLAN = P("docs/implementation-plan.md")
DEPLOYMENT = P("docs/deployment.md")
PACKAGING = P("docs/packaging.md")
FOCUS = P("state/current-focus.md")
PROGRESS = P("state/progress.md")
HANDOFF_STATE = P("state/handoff.md")
CHANGE_REQUESTS = P("state/change-requests.md")
ADR16 = P("docs/decisions/0016-launcher-assisted-restore.md")
ADR18 = P("docs/decisions/0018-launcher-restore-interaction-and-validation-session.md")

A1 = P("launcher/restore/validation_session.py")
A1_SCRATCH = P("launcher/restore/validation_scratch.py")
A2_PROTOCOL = P("launcher/restore/control_protocol.py")
A2_SESSION = P("launcher/restore/control_session.py")
A2_PLANE = P("launcher/restore/control_plane.py")
A3_PICKER = P("launcher/restore/macos_picker.py")
A3_PICKER_TESTS = P("launcher/tests/test_restore_native_picker.py")
A3_SESSION_TESTS = P("launcher/tests/test_restore_native_picker_session.py")
A3_RUNTIME_TESTS = P("launcher/tests/test_restore_native_picker_runtime.py")
A3_SMOKE = P("scripts/smoke_restore_native_picker.py")

LAUNCHER_RUNTIME = P("launcher/runtime.py")
A4_HANDOFF = P("launcher/restore/browser_handoff.py")
A4_HANDOFF_TESTS = P("launcher/tests/test_restore_browser_handoff.py")
A4_RUNTIME_TESTS = P("launcher/tests/test_restore_control_runtime.py")
INDEX = P("frontend/index.html")
PACKAGE = P("frontend/package.json")
MAIN_TS = P("frontend/src/main.ts")
ROUTES = P("frontend/src/app-navigation-routes.ts")
CONTRACT = P("frontend/src/restore-control-contract.ts")
BROWSER_RUNTIME = P("frontend/src/restore-control-runtime.ts")
PRESENTATION = P("frontend/src/restore-control-presentation.ts")
ENTRY = P("frontend/src/restore-control-entry.ts")
TS_CONFIG = P("frontend/tsconfig.test.restore-control.json")
FRONTEND_TESTS = P("frontend/test/restore-control.test.mjs")
NODE_SMOKE = P("frontend/scripts/smoke-restore-control-client.mjs")
A4_SMOKE = P("scripts/smoke_restore_browser_session.py")

EXPECTED_MAIN_BLOB = "ea98a76638bddcb5a92b9ba31941508f8a816d42"

ACTIVE = (README, PLAN, FOCUS, PROGRESS, HANDOFF_STATE, CHANGE_REQUESTS)
SUPPORTING = (CURRENT, SLICES, PROFILE, DEPLOYMENT, PACKAGING)
CORE = (
    "PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED",
    "PR #179 — MERGED — A3 CLOSED / A4 AUTHORIZED",
    "C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN",
    "C4-II-A — IN PROGRESS — SLICED",
    "C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A4 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
    "C4-II-B — PLANNED — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)
STALE = (
    "C4-II-A4 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "A4 is the **only authorized next runtime slice**",
    "A4 implementation is absent from closure branch",
)

HISTORY = (
    P("docs/history/AGENTS.md"), P("docs/history/README.md"),
    P("docs/history/project-timeline-through-pr170.md"),
    P("docs/history/c4-i-implementation-and-audit-history.md"),
    P("docs/history/implementation-plan/2026-08-06-pre-compaction.md"),
    P("docs/history/state-snapshots/2026-08-06-c4-i-closure/current-focus.md"),
    P("docs/history/state-snapshots/2026-08-06-c4-i-closure/progress.md"),
    P("docs/history/state-snapshots/2026-08-06-c4-i-closure/handoff.md"),
    P("docs/history/change-requests/2026-08-06-pre-compaction.md"),
)
HISTORY_BLOBS = {
    P("docs/history/implementation-plan/2026-08-06-pre-compaction.md"): "763a720ac7cc30c9eb870c5f24fa23aee75ea054",
    P("docs/history/state-snapshots/2026-08-06-c4-i-closure/current-focus.md"): "3fcd869815a7559cc46f278b37ee06eae683dd75",
    P("docs/history/state-snapshots/2026-08-06-c4-i-closure/progress.md"): "fcc0479d15cefa1672d01939418b9c37152559d7",
    P("docs/history/state-snapshots/2026-08-06-c4-i-closure/handoff.md"): "e47f8872415ada073d5518c5bd24dace20ff5fe4",
    P("docs/history/change-requests/2026-08-06-pre-compaction.md"): "85f284b0a08eba2a2f084672091cc9eedab261dc",
}

DESTRUCTIVE_MODULES = {"launcher.restore.engine", "launcher.restore.state", "launcher.restore.safety_copy", "launcher.restore.replacement", "launcher.restore.recovery", "launcher.restore.phases"}
DESTRUCTIVE_CALLS = {"execute_restore", "create_verified_safety_copy", "commit_replacement", "prepare_replacement_artifact", "quiesce_target_journal", "recover_incomplete_restore", "perform_rollback"}
ERRORS: list[str] = []


def fail(message: str) -> None: ERRORS.append(message)

def read(path: Path) -> str:
    try: return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")
        return ""

def norm(value: str) -> str: return " ".join(value.split()).casefold()

def require(path: Path, markers: tuple[str, ...]) -> None:
    text = norm(read(path))
    for marker in markers:
        if norm(marker) not in text: fail(f"{path.relative_to(ROOT)} is missing marker: {marker!r}")

def blob(path: Path) -> str:
    data = path.read_bytes(); return sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def parse(path: Path) -> ast.AST | None:
    text = read(path)
    if not text: return None
    try: return ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        fail(f"{path.relative_to(ROOT)} does not parse: {exc}"); return None

def modules(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): out.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module: out.add(node.module)
    return out

def calls(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name): out.add(node.func.id)
            elif isinstance(node.func, ast.Attribute): out.add(node.func.attr)
    return out

def function(tree: ast.AST, name: str) -> str:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name: return ast.unparse(node)
    fail(f"missing function {name!r}"); return ""

def no_destructive(path: Path, extra: set[str] | None = None) -> None:
    tree = parse(path)
    if tree is None: return
    forbidden = set(DESTRUCTIVE_MODULES); forbidden.update(extra or set())
    for item in sorted(modules(tree) & forbidden): fail(f"{path.relative_to(ROOT)} imports forbidden scope: {item}")
    for item in sorted(calls(tree) & DESTRUCTIVE_CALLS): fail(f"{path.relative_to(ROOT)} calls destructive boundary: {item}")


def check_docs() -> None:
    for path in ACTIVE: require(path, CORE)
    require(CURRENT, CORE + ("72b04510efd6d1f104369a450ed1c4d4dfe063ad", "52cc0b04e0b9531b6cc234c83cbcbb81e04a37bf", "full backend + launcher: 2457 passed", "history.state", EXPECTED_MAIN_BLOB, "No PASS is claimed until these run on the final published A4 head"))
    require(SLICES, ("A4 — Browser Restore screen and non-destructive E2E flow — CURRENT IMPLEMENTATION", "/backups/restore", "history.state", "sessionStorage", "C4-II-B — PLANNED — NOT AUTHORIZED"))
    require(PROFILE, ("A3→A4 browser seam — CURRENT IMPLEMENTATION", "POST /v1/bootstrap", "history.replaceState", "history.state", "sessionStorage", "C4-II-B remains separately not authorized"))
    require(DEPLOYMENT, ("C4-II-A4 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED", "/usr/bin/osascript", "fragment only", "sessionStorage"))
    require(PACKAGING, ("C4-II-A4 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED", "Mac App Store sandbox compatibility is **not claimed**", "restore-control-entry.js", "main.js"))
    for path in ACTIVE + SUPPORTING:
        text = norm(read(path))
        for stale in STALE:
            if norm(stale) in text: fail(f"{path.relative_to(ROOT)} retains stale pre-A4 phrase: {stale!r}")


def check_history() -> None:
    require(ADR16, ("before_restore", "replacement_intent", "recovery_blocked"))
    require(ADR18, ("127.0.0.1", "/backups/restore", "/usr/bin/osascript", "#cw-control=<ephemeral-port>:<bootstrap-token>", "sessionStorage", "heartbeat interval: 15 seconds", "control-session expiry: 60 seconds"))
    for path in HISTORY:
        if not path.exists(): fail(f"missing required history path: {path.relative_to(ROOT)}")
    for path, expected in HISTORY_BLOBS.items():
        if path.exists() and blob(path) != expected: fail(f"protected history blob changed: {path.relative_to(ROOT)}")


def check_predecessors() -> None:
    for path in (A1, A1_SCRATCH): no_destructive(path, {"http.server", "socket", "subprocess", "webbrowser"})
    require(A1, ("RestoreCandidatePreparationService", "prepare_restore_candidate", "open_selected_source", "stage_source", "validate_staged_candidate", "SourceIdentity", "retained_proof"))
    for path in (A2_PROTOCOL, A2_SESSION, A2_PLANE): no_destructive(path, {"subprocess", "webbrowser"})
    require(A2_PROTOCOL, ("SourceSelectionAdapter", "UnavailableSourceSelectionAdapter", "ControlStateSnapshot", "CommandReply"))
    require(A2_SESSION, ("BOOTSTRAP_RANDOM_BYTES = 32", "SESSION_RANDOM_BYTES = 32", "HEARTBEAT_INTERVAL_SECONDS = 15", "SESSION_EXPIRY_SECONDS = 60", "_consume_command_locked", "action_in_progress", "command_sequence_stale", "command_sequence_future", "command_sequence_conflict", "guarantees stale A1 authority is gone before quiescence", "worker.join()"))
    require(A2_PLANE, ("CONTROL_HOST = \"127.0.0.1\"", "/v1/bootstrap", "/v1/state", "/v1/heartbeat", "/v1/restore/select", "/v1/restore/cancel", "Cache-Control", "no-store", "REQUEST_ID_PATTERN"))
    no_destructive(A3_PICKER)
    require(A3_PICKER, ("OSASCRIPT_PATH = Path(\"/usr/bin/osascript\")", "PICKER_CANCELLED_SENTINEL", "use scripting additions", "choose file", "on error number -128", "shell=False", "process.terminate()", "process.kill()", "selected_path.is_absolute()"))
    for marker in ("System Events", "shell=True", "/backups/restore", "execute_restore("):
        if marker in read(A3_PICKER): fail(f"A3 picker contains forbidden marker: {marker!r}")
    require(A3_PICKER_TESTS, ("test_selected_path_uses_exact_owned_osascript_command", "test_cancel_terminates_and_reaps_owned_picker_process", "test_terminate_timeout_kills_and_reaps_owned_picker_process", "test_natural_exit_between_poll_and_terminate_is_reaped_as_cancel"))
    require(A3_SESSION_TESTS, ("test_control_cancel_terminates_owned_native_picker_process", "test_session_expiry_terminates_owned_native_picker_process", "test_native_selected_path_flows_only_through_a1_candidate_preparation", "test_picker_stderr_and_raw_path_never_cross_safe_control_state"))
    require(A3_RUNTIME_TESTS, ("test_start_restore_control_plane_uses_production_native_picker",))
    require(A3_SMOKE, ("PASS — C4-II-A3 NATIVE MACOS PICKER SMOKE PASSED",))


def check_a4_launcher() -> None:
    no_destructive(A4_HANDOFF, {"subprocess", "webbrowser"})
    require(A4_HANDOFF, ("runtime_config_with_restore_handoff", "urlsplit", "urlunsplit", "replace(config", "cw-control=", "parsed.query", "parsed.fragment", "bootstrap_capability"))
    for marker in ("print(", "logging", "execute_restore", "before_restore"):
        if marker in read(A4_HANDOFF): fail(f"A4 browser handoff contains forbidden marker: {marker!r}")
    tree = parse(LAUNCHER_RUNTIME)
    if tree is not None:
        browser = function(tree, "open_runtime_browser")
        for marker in ("config.frontend_url", "config.backend_url", "webbrowser.open(target_url)"):
            if marker not in browser: fail(f"open_runtime_browser drifted: {marker!r}")
        for marker in ("bootstrap", "session_token", "control_origin"):
            if marker in browser: fail(f"open_runtime_browser directly owns A4 secret logic: {marker!r}")
        locked = function(tree, "_run_locked_runtime")
        first = [locked.find(marker) for marker in ("context.backend.start", "start_restore_control_plane", "runtime_config_with_restore_handoff", "open_runtime_browser(browser_config)")]
        if any(pos < 0 for pos in first) or first != sorted(first): fail("launcher A4 startup ordering drifted")
        final_close = locked.rfind("control_plane.close()")
        backend_stop = locked.rfind("context.backend.stop()")
        if final_close < first[-1] or backend_stop < final_close: fail("launcher A4 shutdown ordering drifted")
    require(A4_HANDOFF_TESTS, ("test_handoff_uses_fragment_only_and_does_not_mutate_original_config", "test_handoff_refuses_non_exact_frontend_origin", "test_handoff_refuses_invalid_control_descriptor"))
    require(A4_RUNTIME_TESTS, ("test_control_plane_starts_after_owned_backend_and_closes_before_backend", "test_control_plane_failure_keeps_ordinary_product_available", "test_invalid_handoff_closes_control_and_opens_ordinary_product"))


def check_a4_browser() -> None:
    if blob(MAIN_TS) != EXPECTED_MAIN_BLOB: fail(f"frontend/src/main.ts changed during A4; expected blob {EXPECTED_MAIN_BLOB}")
    index = read(INDEX); entry = "/assets/restore-control-entry.js"; main = "/assets/main.js"
    if entry not in index or main not in index or index.find(entry) > index.find(main): fail("restore-control-entry.js must load before main.js")
    require(ROUTES, ("'/backups/restore': 'Резервные копии'",))
    require(CONTRACT, ("RESTORE_CONTROL_FRAGMENT_PREFIX = '#cw-control='", "RESTORE_SESSION_STORAGE_KEYS", "cw.restore.control_origin", "cw.restore.run_id", "cw.restore.session_token", "RESTORE_HISTORY_STATE_KEY", "parseRestoreBootstrapFragment", "captureRestoreBootstrap", "exactKeys", "newRestoreRequestId", "readRestoreReplayState"))
    require(BROWSER_RUNTIME, ("HEARTBEAT_INTERVAL_SECONDS", "credentials: 'omit'", "cache: 'no-store'", "referrerPolicy: 'no-referrer'", "Authorization", "readRestoreReplayState", "retryPending", "nextCommandSeq", "pending", "command_seq", "generation === 0"))
    require(ENTRY, ("captureRestoreBootstrap", "window.sessionStorage", "MutationObserver", "bootstrapCapture = { kind: 'none' }", "data-restore-action", "history.pushState", "restoreFocusOwned"))
    require(PRESENTATION, ("Восстановление из резервной копии", "Рабочие данные не изменены", "восстановление ещё не запускалось", "Восстановить из резервной копии"))
    require(PACKAGE, ("test:restore-control", "tsconfig.test.restore-control.json"))
    require(TS_CONFIG, ("restore-control-contract.ts", "restore-control-runtime.ts", "restore-control-presentation.ts"))
    production = "\n".join(read(path) for path in (CONTRACT, BROWSER_RUNTIME, ENTRY, PRESENTATION))
    for marker in ("localStorage", "source_path", "file_bytes", "upload_blob", "filesystem_handle", "execute_restore", '<input type="file"'):
        if marker in production: fail(f"A4 browser code contains forbidden authority marker: {marker!r}")
    require(FRONTEND_TESTS, ("valid bootstrap fragment is captured and removed synchronously", "bootstrap stores only the three run-scoped session descriptors", "state DTO rejects unexpected fields including filesystem paths", "network-uncertain command retries exact same request id and sequence", "reload resumes strict next sequence from same-tab history state", "reload without replay metadata is fail-closed after any prior generation", "accepted presentation is explicit that destructive Restore has not run", "nested Restore route stays inside the backups shell section"))


def check_a4_smoke() -> None:
    require(NODE_SMOKE, ("captureRestoreBootstrap", "RestoreControlRuntime", "Origin", "runtime.select()", "fragmentRemoved", "storedKeys", "nextCommandSeq"))
    require(A4_SMOKE, ("test:restore-control", "runtime_config_with_restore_handoff", "RestoreControlPlane", "MacOSNativeSourceSelectionAdapter", "retained_proof", "audit_logs", "PASS — C4-II-A4 BROWSER RESTORE SESSION SMOKE PASSED"))
    no_destructive(A4_SMOKE)


def main() -> int:
    check_docs(); check_history(); check_predecessors(); check_a4_launcher(); check_a4_browser(); check_a4_smoke()
    if ERRORS:
        print("Documentation lifecycle consistency: FAIL")
        for error in ERRORS: print(f"- {error}")
        return 1
    print("Documentation lifecycle consistency: PASS")
    print(f"Checked {len(ACTIVE)} compact active files.")
    print(f"Verified {len(HISTORY)} required history paths.")
    print(f"Verified {len(HISTORY_BLOBS)} exact historical Git blob identities.")
    print("Verified PR #179 merged / C4-II-A4 authorization baseline.")
    print("Verified C4-II-A4 current-changeset launcher fragment-handoff boundary.")
    print("Verified fragment removal, sessionStorage allowlist and same-tab replay contract.")
    print("Verified /backups/restore pathless non-destructive browser presentation boundary.")
    print("Verified frontend/src/main.ts remains byte-identical and A4 stays outside the shell monolith.")
    print("Verified A4 cross-layer smoke/test contracts are present.")
    print("Verified closed A1/A2/A3 boundaries remain intact.")
    print("Verified C4-II-B destructive Restore remains not authorized.")
    print("Verified ADR 0016 / ADR 0018 durable authority remains unchanged.")
    print("Verified maintained historical guidance and exact snapshots remain protected.")
    return 0

if __name__ == "__main__": sys.exit(main())
