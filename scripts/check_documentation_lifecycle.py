#!/usr/bin/env python3
"""Guard A4 closure, B1-only authorization, and closed Restore boundaries."""

from __future__ import annotations

import ast
from hashlib import sha1
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
P = lambda value: ROOT / value

README = P("README.md")
CURRENT = P("docs/current-lifecycle.md")
A_SLICES = P("docs/c4-ii-a-implementation-slices.md")
B_SLICES = P("docs/c4-ii-b-implementation-slices.md")
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

ENGINE = P("launcher/restore/engine.py")
CONTRACTS = P("launcher/restore/contracts.py")
STAGING = P("launcher/restore/staging.py")
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
BROWSER_CONTRACT = P("frontend/src/restore-control-contract.ts")
BROWSER_RUNTIME = P("frontend/src/restore-control-runtime.ts")
PRESENTATION = P("frontend/src/restore-control-presentation.ts")
ENTRY = P("frontend/src/restore-control-entry.ts")
TS_CONFIG = P("frontend/tsconfig.test.restore-control.json")
FRONTEND_TESTS = P("frontend/test/restore-control.test.mjs")
FRONTEND_RACE_TESTS = P("frontend/test/restore-control-races.test.mjs")
NODE_SMOKE = P("frontend/scripts/smoke-restore-control-client.mjs")
A4_SMOKE = P("scripts/smoke_restore_browser_session.py")

EXPECTED_MAIN_BLOB = "ea98a76638bddcb5a92b9ba31941508f8a816d42"
# Closure branch must not contain B1 implementation. These are the exact runtime
# blobs merged by PR #180; the next B1 implementation PR is allowed to change
# them only after this authorization branch itself is merged.
EXPECTED_ENGINE_BLOB = "7113ac162bc3aab36ae3e63e835a5b4c5bdc16b5"
EXPECTED_CONTRACTS_BLOB = "b4fcd9e4bad34024fe735cdd1d998e018a16511a"
EXPECTED_STAGING_BLOB = "3126d5b1e68e764c135739fad71915912481c493"
EXPECTED_A1_BLOB = "c8734ab60a576ecad53acd961571ddf2c14bdcf4"

ACTIVE = (README, PLAN, FOCUS, PROGRESS, HANDOFF_STATE, CHANGE_REQUESTS)
SUPPORTING = (CURRENT, A_SLICES, B_SLICES, PROFILE, DEPLOYMENT, PACKAGING)
CORE = (
    "PR #180 — MERGED — C4-II-A4 EXACT-HEAD VERIFIED",
    "C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN",
    "C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B — IN PROGRESS — SLICED",
    "C4-II-B1 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-B2 — PLANNED — NOT AUTHORIZED",
    "C4-II-B3 — PLANNED — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)
STALE = (
    "C4-II-A — IN PROGRESS — SLICED",
    "C4-II-A4 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
    "C4-II-A4 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-B — PLANNED — NOT AUTHORIZED",
    "A4 still requires exact-head",
    "Manual UI review — REQUIRED / PENDING",
)

HISTORY = (
    P("docs/history/AGENTS.md"),
    P("docs/history/README.md"),
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

DESTRUCTIVE_MODULES = {
    "launcher.restore.engine",
    "launcher.restore.state",
    "launcher.restore.safety_copy",
    "launcher.restore.replacement",
    "launcher.restore.recovery",
    "launcher.restore.phases",
}
DESTRUCTIVE_CALLS = {
    "execute_restore",
    "create_verified_safety_copy",
    "commit_replacement",
    "prepare_replacement_artifact",
    "quiesce_target_journal",
    "recover_incomplete_restore",
    "perform_rollback",
}
ERRORS: list[str] = []


def fail(message: str) -> None:
    ERRORS.append(message)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")
        return ""


def norm(value: str) -> str:
    return " ".join(value.split()).casefold()


def require(path: Path, markers: tuple[str, ...]) -> None:
    text = norm(read(path))
    for marker in markers:
        if norm(marker) not in text:
            fail(f"{path.relative_to(ROOT)} is missing marker: {marker!r}")


def blob(path: Path) -> str:
    data = path.read_bytes()
    return sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def parse(path: Path) -> ast.AST | None:
    text = read(path)
    if not text:
        return None
    try:
        return ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        fail(f"{path.relative_to(ROOT)} does not parse: {exc}")
        return None


def modules(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def calls(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                out.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                out.add(node.func.attr)
    return out


def function(tree: ast.AST, name: str) -> str:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.unparse(node)
    fail(f"missing function {name!r}")
    return ""


def no_destructive(path: Path, extra: set[str] | None = None) -> None:
    tree = parse(path)
    if tree is None:
        return
    forbidden = set(DESTRUCTIVE_MODULES)
    forbidden.update(extra or set())
    for item in sorted(modules(tree) & forbidden):
        fail(f"{path.relative_to(ROOT)} imports forbidden scope: {item}")
    for item in sorted(calls(tree) & DESTRUCTIVE_CALLS):
        fail(f"{path.relative_to(ROOT)} calls destructive boundary: {item}")


def check_docs() -> None:
    for path in ACTIVE:
        require(path, CORE)
    require(
        CURRENT,
        CORE
        + (
            "79c698ed76d478d608a25f4b95499ff519794228",
            "e61d4e233c98d3c53e7749fe96ed0ee630610372",
            "full backend + launcher: 2470 passed",
            "frontend A4: 16 passed",
            "desktop, narrow-window, keyboard/focus and real macOS picker UI smoke: PASS",
            EXPECTED_MAIN_BLOB,
            "same `HeldSource` descriptor",
        ),
    )
    require(
        A_SLICES,
        (
            "CLOSED NORMATIVE IMPLEMENTATION PLAN",
            "C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED",
            "PR #180 reviewed head",
            "frontend A4 16",
            "docs/c4-ii-b-implementation-slices.md",
        ),
    )
    require(
        B_SLICES,
        CORE
        + (
            "B1 — Bind retained source proof into C4-I intake — AUTHORIZED NEXT",
            "HeldSource.revalidate()",
            "HeldSource.assert_still_self_contained()",
            "HeldSource.digest()",
            "before `prepared` exists",
            "B2 — Launcher destructive coordinator/control command — PLANNED — NOT AUTHORIZED",
            "B3 — Browser explicit destructive confirmation — PLANNED — NOT AUTHORIZED",
        ),
    )
    require(
        PROFILE,
        CORE
        + (
            "Authorized B1 seam — proof binding at C4-I intake",
            "same `HeldSource` descriptor",
            "A path-only pre-check followed by a later re-open is forbidden",
        ),
    )
    require(DEPLOYMENT, ("PR #180 — MERGED — C4-II-A4 EXACT-HEAD VERIFIED", "B1 deployment consequence", "/usr/bin/osascript", "sessionStorage"))
    require(PACKAGING, ("PR #180 — MERGED — C4-II-A4 EXACT-HEAD VERIFIED", "B1 packaging consequence", "Mac App Store sandbox compatibility is **not claimed**", "restore-control-entry.js", "main.js"))

    for path in ACTIVE + SUPPORTING:
        text = norm(read(path))
        for stale in STALE:
            if norm(stale) in text:
                fail(f"{path.relative_to(ROOT)} retains stale lifecycle phrase: {stale!r}")


def check_history() -> None:
    require(ADR16, ("before_restore", "replacement_intent", "recovery_blocked", "selected source", "immutable"))
    require(
        ADR18,
        (
            "127.0.0.1",
            "/backups/restore",
            "/usr/bin/osascript",
            "#cw-control=<ephemeral-port>:<bootstrap-token>",
            "sessionStorage",
            "heartbeat interval: 15 seconds",
            "control-session expiry: 60 seconds",
            "compare descriptor/path SourceIdentity",
            "recompute and compare full SHA-256",
        ),
    )
    for path in HISTORY:
        if not path.exists():
            fail(f"missing required history path: {path.relative_to(ROOT)}")
    for path, expected in HISTORY_BLOBS.items():
        if path.exists() and blob(path) != expected:
            fail(f"protected history blob changed: {path.relative_to(ROOT)}")


def check_a1_a2_a3() -> None:
    for path in (A1, A1_SCRATCH):
        no_destructive(path, {"http.server", "socket", "subprocess", "webbrowser"})
    require(A1, ("RestoreCandidatePreparationService", "RetainedSourceProof", "SourceIdentity", "sha256", "retained_proof", "prepare_restore_candidate"))

    for path in (A2_PROTOCOL, A2_SESSION, A2_PLANE):
        no_destructive(path, {"subprocess", "webbrowser"})
    require(A2_PROTOCOL, ("SourceSelectionAdapter", "ControlStateSnapshot", "CommandReply"))
    require(A2_SESSION, ("BOOTSTRAP_RANDOM_BYTES = 32", "SESSION_RANDOM_BYTES = 32", "HEARTBEAT_INTERVAL_SECONDS = 15", "SESSION_EXPIRY_SECONDS = 60", "_consume_command_locked", "command_sequence_conflict", "worker.join()"))
    require(A2_PLANE, ("CONTROL_HOST = \"127.0.0.1\"", "/v1/bootstrap", "/v1/state", "/v1/heartbeat", "/v1/restore/select", "/v1/restore/cancel", "Cache-Control", "no-store"))

    no_destructive(A3_PICKER)
    require(A3_PICKER, ("OSASCRIPT_PATH = Path(\"/usr/bin/osascript\")", "use scripting additions", "choose file", "on error number -128", "shell=False", "process.terminate()", "process.kill()", "selected_path.is_absolute()"))
    for marker in ("System Events", "shell=True", "execute_restore("):
        if marker in read(A3_PICKER):
            fail(f"A3 picker contains forbidden marker: {marker!r}")
    require(A3_PICKER_TESTS, ("test_selected_path_uses_exact_owned_osascript_command", "test_cancel_terminates_and_reaps_owned_picker_process"))
    require(A3_SESSION_TESTS, ("test_control_cancel_terminates_owned_native_picker_process", "test_native_selected_path_flows_only_through_a1_candidate_preparation", "test_picker_stderr_and_raw_path_never_cross_safe_control_state"))
    require(A3_RUNTIME_TESTS, ("test_start_restore_control_plane_uses_production_native_picker",))
    require(A3_SMOKE, ("PASS — C4-II-A3 NATIVE MACOS PICKER SMOKE PASSED",))


def check_a4_closed() -> None:
    if blob(MAIN_TS) != EXPECTED_MAIN_BLOB:
        fail(f"frontend/src/main.ts changed after A4 closure; expected blob {EXPECTED_MAIN_BLOB}")

    no_destructive(A4_HANDOFF, {"subprocess", "webbrowser"})
    require(A4_HANDOFF, ("runtime_config_with_restore_handoff", "cw-control=", "bootstrap_capability", "parsed.query", "parsed.fragment"))

    tree = parse(LAUNCHER_RUNTIME)
    if tree is not None:
        browser = function(tree, "open_runtime_browser")
        for marker in ("config.frontend_url", "config.backend_url", "webbrowser.open(target_url)"):
            if marker not in browser:
                fail(f"open_runtime_browser drifted: {marker!r}")
        locked = function(tree, "_run_locked_runtime")
        order = [locked.find(marker) for marker in ("context.backend.start", "start_restore_control_plane", "runtime_config_with_restore_handoff", "open_runtime_browser(browser_config)")]
        if any(pos < 0 for pos in order) or order != sorted(order):
            fail("launcher A4 startup ordering drifted")

    index = read(INDEX)
    entry_script = "/assets/restore-control-entry.js"
    main_script = "/assets/main.js"
    if entry_script not in index or main_script not in index or index.find(entry_script) > index.find(main_script):
        fail("restore-control-entry.js must load before main.js")

    require(ROUTES, ("'/backups/restore': 'Резервные копии'",))
    require(BROWSER_CONTRACT, ("RESTORE_CONTROL_FRAGMENT_PREFIX = '#cw-control='", "RESTORE_SESSION_STORAGE_KEYS", "RESTORE_HISTORY_STATE_KEY", "captureRestoreBootstrap", "newRestoreRequestId"))
    require(BROWSER_RUNTIME, ("credentials: 'omit'", "cache: 'no-store'", "referrerPolicy: 'no-referrer'", "Authorization", "retryPending", "nextCommandSeq", "pending", "command_seq"))
    require(ENTRY, ("captureRestoreBootstrap", "window.sessionStorage", "MutationObserver", "bootstrapCapture = { kind: 'none' }", "data-restore-action"))
    require(PRESENTATION, ("Восстановление из резервной копии", "Рабочие данные не изменены", "восстановление ещё не запускалось", "Восстановить из резервной копии"))
    require(PACKAGE, ("test:restore-control", "restore-control-races.test.mjs"))
    require(TS_CONFIG, ("restore-control-contract.ts", "restore-control-runtime.ts", "restore-control-presentation.ts"))
    require(FRONTEND_TESTS, ("valid bootstrap fragment is captured and removed synchronously", "accepted presentation is explicit that destructive Restore has not run"))
    require(FRONTEND_RACE_TESTS, ("network-uncertain one-use bootstrap is restart-only, never retry guidance", "late state response is ignored after a concurrent request invalidates the session"))
    require(NODE_SMOKE, ("captureRestoreBootstrap", "RestoreControlRuntime", "runtime.select()", "fragmentRemoved", "storedKeys", "nextCommandSeq"))
    require(A4_SMOKE, ("RestoreControlPlane", "MacOSNativeSourceSelectionAdapter", "retained_proof", "audit_logs", "PASS — C4-II-A4 BROWSER RESTORE SESSION SMOKE PASSED"))
    no_destructive(A4_SMOKE)

    production = "\n".join(read(path) for path in (BROWSER_CONTRACT, BROWSER_RUNTIME, ENTRY, PRESENTATION))
    for marker in ("localStorage", "source_path", "file_bytes", "upload_blob", "filesystem_handle", "execute_restore", '<input type="file"'):
        if marker in production:
            fail(f"A4 browser code contains forbidden authority marker: {marker!r}")

    # C4-II-A control vocabulary remains non-destructive until a later B2
    # authorization explicitly changes it.
    plane_text = read(A2_PLANE)
    for marker in ("/v1/restore/confirm", "/v1/restore/execute"):
        if marker in plane_text:
            fail(f"B2 control command leaked into A4 closure branch: {marker}")


def check_b1_authorization_only() -> None:
    expected = {
        ENGINE: EXPECTED_ENGINE_BLOB,
        CONTRACTS: EXPECTED_CONTRACTS_BLOB,
        STAGING: EXPECTED_STAGING_BLOB,
        A1: EXPECTED_A1_BLOB,
    }
    for path, expected_blob in expected.items():
        if blob(path) != expected_blob:
            fail(f"B1 runtime implementation leaked into closure branch: {path.relative_to(ROOT)}")

    require(ENGINE, ("execute_restore", "open_selected_source", "stage_source", "validate_staged_candidate", "create_verified_safety_copy", "replacement_intent"))
    require(STAGING, ("class HeldSource", "def revalidate", "def digest", "def assert_still_self_contained", "open_selected_source", "stage_source"))
    require(CONTRACTS, ("class RestoreRequest", "selected_source: Path", "class RestoreResult"))


def main() -> int:
    check_docs()
    check_history()
    check_a1_a2_a3()
    check_a4_closed()
    check_b1_authorization_only()

    if ERRORS:
        print("Documentation lifecycle consistency: FAIL")
        for error in ERRORS:
            print(f"- {error}")
        return 1

    print("Documentation lifecycle consistency: PASS")
    print(f"Checked {len(ACTIVE)} compact active files.")
    print(f"Verified {len(HISTORY)} required history paths.")
    print(f"Verified {len(HISTORY_BLOBS)} exact historical Git blob identities.")
    print("Verified PR #180 merged / C4-II-A4 exact-head closure evidence.")
    print("Verified C4-II-A is DONE and its A1/A2/A3/A4 boundaries remain intact.")
    print("Verified A4 fragment/session/pathless browser contract and race regressions remain present.")
    print("Verified frontend/src/main.ts remains byte-identical after A4 closure.")
    print("Verified B1 is the only authorized next implementation slice.")
    print("Verified B1 source-proof binding is specified against the same C4-I HeldSource descriptor.")
    print("Verified no B1 runtime implementation leaked into this closure branch.")
    print("Verified B2/B3 destructive coordinator/confirmation remain not authorized.")
    print("Verified ADR 0016 / ADR 0018 durable authority remains unchanged.")
    print("Verified maintained historical guidance and exact snapshots remain protected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
