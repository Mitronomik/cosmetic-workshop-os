#!/usr/bin/env python3
"""Check post-C4-II-A3 closure and C4-II-A4 authorization boundaries."""

from __future__ import annotations

import ast
from hashlib import sha1
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

README = ROOT / "README.md"
CURRENT_PROFILE = ROOT / "docs/current-lifecycle.md"
SLICE_PLAN = ROOT / "docs/c4-ii-a-implementation-slices.md"
RESTORE_PROFILE = ROOT / "docs/restore-interaction-and-validation-session.md"
IMPLEMENTATION_PLAN = ROOT / "docs/implementation-plan.md"
DEPLOYMENT = ROOT / "docs/deployment.md"
PACKAGING = ROOT / "docs/packaging.md"
CURRENT_FOCUS = ROOT / "state/current-focus.md"
PROGRESS = ROOT / "state/progress.md"
HANDOFF = ROOT / "state/handoff.md"
CHANGE_REQUESTS = ROOT / "state/change-requests.md"
ADR_0016 = ROOT / "docs/decisions/0016-launcher-assisted-restore.md"
ADR_0018 = ROOT / "docs/decisions/0018-launcher-restore-interaction-and-validation-session.md"

A1_SESSION = ROOT / "launcher/restore/validation_session.py"
A1_SCRATCH = ROOT / "launcher/restore/validation_scratch.py"
A2_PROTOCOL = ROOT / "launcher/restore/control_protocol.py"
A2_SESSION = ROOT / "launcher/restore/control_session.py"
A2_PLANE = ROOT / "launcher/restore/control_plane.py"
A3_PICKER = ROOT / "launcher/restore/macos_picker.py"
A3_PICKER_TESTS = ROOT / "launcher/tests/test_restore_native_picker.py"
A3_SESSION_TESTS = ROOT / "launcher/tests/test_restore_native_picker_session.py"
A3_RUNTIME_TESTS = ROOT / "launcher/tests/test_restore_native_picker_runtime.py"
A3_SMOKE = ROOT / "scripts/smoke_restore_native_picker.py"
RUNTIME = ROOT / "launcher/runtime.py"
FRONTEND_ROUTES = ROOT / "frontend/src/app-navigation-routes.ts"

COMPACT_ACTIVE_FILES = (
    README,
    IMPLEMENTATION_PLAN,
    CURRENT_FOCUS,
    PROGRESS,
    HANDOFF,
    CHANGE_REQUESTS,
)
SUPPORTING_ACTIVE_FILES = (
    CURRENT_PROFILE,
    SLICE_PLAN,
    RESTORE_PROFILE,
    DEPLOYMENT,
    PACKAGING,
)

REQUIRED_HISTORY = (
    ROOT / "docs/history/AGENTS.md",
    ROOT / "docs/history/README.md",
    ROOT / "docs/history/project-timeline-through-pr170.md",
    ROOT / "docs/history/c4-i-implementation-and-audit-history.md",
    ROOT / "docs/history/implementation-plan/2026-08-06-pre-compaction.md",
    ROOT / "docs/history/state-snapshots/2026-08-06-c4-i-closure/current-focus.md",
    ROOT / "docs/history/state-snapshots/2026-08-06-c4-i-closure/progress.md",
    ROOT / "docs/history/state-snapshots/2026-08-06-c4-i-closure/handoff.md",
    ROOT / "docs/history/change-requests/2026-08-06-pre-compaction.md",
)
EXPECTED_HISTORY_BLOBS = {
    ROOT / "docs/history/implementation-plan/2026-08-06-pre-compaction.md": "763a720ac7cc30c9eb870c5f24fa23aee75ea054",
    ROOT / "docs/history/state-snapshots/2026-08-06-c4-i-closure/current-focus.md": "3fcd869815a7559cc46f278b37ee06eae683dd75",
    ROOT / "docs/history/state-snapshots/2026-08-06-c4-i-closure/progress.md": "fcc0479d15cefa1672d01939418b9c37152559d7",
    ROOT / "docs/history/state-snapshots/2026-08-06-c4-i-closure/handoff.md": "e47f8872415ada073d5518c5bd24dace20ff5fe4",
    ROOT / "docs/history/change-requests/2026-08-06-pre-compaction.md": "85f284b0a08eba2a2f084672091cc9eedab261dc",
}

CORE_CURRENT_MARKERS = (
    "PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED",
    "C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN",
    "C4-II-A — IN PROGRESS — SLICED",
    "C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A4 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-B — PLANNED — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)
STALE_ACTIVE_PHRASES = (
    "C4-II-A3 — IMPLEMENTED IN CURRENT CHANGESET",
    "C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE",
    "A3 is implemented only in the current changeset",
    "A4 remains blocked until A3",
)

FORBIDDEN_DESTRUCTIVE_MODULES = {
    "launcher.restore.engine",
    "launcher.restore.state",
    "launcher.restore.safety_copy",
    "launcher.restore.replacement",
    "launcher.restore.recovery",
    "launcher.restore.phases",
}
FORBIDDEN_DESTRUCTIVE_CALLS = {
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


def normalized(text: str) -> str:
    return " ".join(text.split()).casefold()


def has_marker(text: str, marker: str) -> bool:
    return normalized(marker) in normalized(text)


def require_markers(path: Path, markers: tuple[str, ...]) -> None:
    text = read(path)
    for marker in markers:
        if not has_marker(text, marker):
            fail(f"{path.relative_to(ROOT)} is missing marker: {marker!r}")


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def parse_python(path: Path) -> ast.AST | None:
    text = read(path)
    if not text:
        return None
    try:
        return ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        fail(f"{path.relative_to(ROOT)} does not parse: {exc}")
        return None


def imported_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def called_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                names.add(node.func.attr)
    return names


def function_unparse(tree: ast.AST, name: str) -> str:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.unparse(node)
    fail(f"missing function {name!r}")
    return ""


def check_no_destructive_calls(path: Path, extra_forbidden_modules: set[str] | None = None) -> None:
    tree = parse_python(path)
    if tree is None:
        return
    modules = set(FORBIDDEN_DESTRUCTIVE_MODULES)
    modules.update(extra_forbidden_modules or set())
    for module in sorted(imported_modules(tree) & modules):
        fail(f"{path.relative_to(ROOT)} imports forbidden scope: {module}")
    for name in sorted(called_names(tree) & FORBIDDEN_DESTRUCTIVE_CALLS):
        fail(f"{path.relative_to(ROOT)} calls destructive boundary: {name}")


def check_documentation_state() -> None:
    for path in COMPACT_ACTIVE_FILES:
        require_markers(path, CORE_CURRENT_MARKERS)

    require_markers(
        CURRENT_PROFILE,
        CORE_CURRENT_MARKERS
        + (
            "b0de148032d9b3d2f9912298897f8649c9b1692b",
            "9d95b0c39c4abd05d5a574c6cd8574b8e457f36b",
            "full backend + launcher: 2457 passed",
            "A4 is the **only authorized next runtime slice**",
            "#cw-control=<ephemeral-port>:<bootstrap-token>",
        ),
    )
    require_markers(
        SLICE_PLAN,
        (
            "A4 — Browser Restore screen and non-destructive E2E flow — AUTHORIZED NEXT",
            "/backups/restore",
            "#cw-control=<ephemeral-port>:<bootstrap-token>",
            "history.replaceState",
            "sessionStorage",
            "localStorage",
            "C4-II-B — PLANNED — NOT AUTHORIZED",
        ),
    )
    require_markers(
        RESTORE_PROFILE,
        (
            "A3→A4 browser seam — AUTHORIZED",
            "/backups/restore",
            "POST /v1/bootstrap",
            "history.replaceState",
            "sessionStorage",
            "C4-II-B remains separately not authorized",
        ),
    )
    require_markers(DEPLOYMENT, ("C4-II-A4 — AUTHORIZED NEXT — NOT IMPLEMENTED", "/usr/bin/osascript", "fragment only"))
    require_markers(PACKAGING, ("C4-II-A4 — AUTHORIZED NEXT — NOT IMPLEMENTED", "Mac App Store sandbox compatibility is **not claimed**", "sessionStorage"))

    for path in COMPACT_ACTIVE_FILES + SUPPORTING_ACTIVE_FILES:
        text = read(path)
        for phrase in STALE_ACTIVE_PHRASES:
            if has_marker(text, phrase):
                fail(f"{path.relative_to(ROOT)} retains stale pre-A3-closure phrase: {phrase!r}")


def check_durable_authority_and_history() -> None:
    require_markers(ADR_0016, ("before_restore", "replacement_intent", "recovery_blocked"))
    require_markers(
        ADR_0018,
        (
            "127.0.0.1",
            "/backups/restore",
            "/usr/bin/osascript",
            "#cw-control=<ephemeral-port>:<bootstrap-token>",
            "sessionStorage",
            "heartbeat interval: 15 seconds",
            "control-session expiry: 60 seconds",
        ),
    )
    for path in REQUIRED_HISTORY:
        if not path.exists():
            fail(f"missing required history path: {path.relative_to(ROOT)}")
    for path, expected in EXPECTED_HISTORY_BLOBS.items():
        if path.exists() and git_blob_sha(path) != expected:
            fail(f"protected history blob changed: {path.relative_to(ROOT)}")


def check_closed_a1_boundary() -> None:
    for path in (A1_SESSION, A1_SCRATCH):
        check_no_destructive_calls(path, {"http.server", "socket", "subprocess", "webbrowser"})
    require_markers(A1_SESSION, ("RestoreCandidatePreparationService", "prepare_restore_candidate", "open_selected_source", "stage_source", "validate_staged_candidate", "SourceIdentity", "retained_proof"))


def check_closed_a2_boundary() -> None:
    for path in (A2_PROTOCOL, A2_SESSION, A2_PLANE):
        check_no_destructive_calls(path, {"subprocess", "webbrowser"})
    require_markers(A2_PROTOCOL, ("SourceSelectionAdapter", "UnavailableSourceSelectionAdapter", "ControlStateSnapshot", "CommandReply"))
    require_markers(
        A2_SESSION,
        (
            "BOOTSTRAP_RANDOM_BYTES = 32",
            "SESSION_RANDOM_BYTES = 32",
            "HEARTBEAT_INTERVAL_SECONDS = 15",
            "SESSION_EXPIRY_SECONDS = 60",
            "hmac.compare_digest",
            "_consume_command_locked",
            "action_in_progress",
            "command_sequence_stale",
            "command_sequence_future",
            "command_sequence_conflict",
            "guarantees stale A1 authority is gone before quiescence",
            "worker.join()",
        ),
    )
    require_markers(A2_PLANE, ("ThreadingHTTPServer", "CONTROL_HOST = \"127.0.0.1\"", "/v1/bootstrap", "/v1/state", "/v1/heartbeat", "/v1/restore/select", "/v1/restore/cancel", "Cache-Control", "no-store", "REQUEST_ID_PATTERN"))
    for browser_authority in ("source_path", "file_bytes", "upload_blob", "filesystem_handle"):
        if browser_authority in read(A2_PLANE):
            fail(f"A2 HTTP boundary contains browser filesystem authority: {browser_authority!r}")


def check_closed_a3_boundary() -> None:
    check_no_destructive_calls(A3_PICKER)
    require_markers(
        A3_PICKER,
        (
            "OSASCRIPT_PATH = Path(\"/usr/bin/osascript\")",
            "PICKER_CANCELLED_SENTINEL",
            "use scripting additions",
            "choose file",
            "POSIX path of selectedFile",
            "on error number -128",
            "shell=False",
            "cancel_event.is_set()",
            "process.terminate()",
            "process.kill()",
            "process.communicate",
            "selected_path.is_absolute()",
            "SourceSelectionResult.selected(selected_path)",
        ),
    )
    for forbidden in ("System Events", "shell=True", "/backups/restore", "execute_restore("):
        if forbidden in read(A3_PICKER):
            fail(f"A3 picker contains forbidden marker: {forbidden!r}")
    require_markers(A3_PICKER_TESTS, ("test_selected_path_uses_exact_owned_osascript_command", "test_cancel_terminates_and_reaps_owned_picker_process", "test_terminate_timeout_kills_and_reaps_owned_picker_process", "test_natural_exit_between_poll_and_terminate_is_reaped_as_cancel"))
    require_markers(A3_SESSION_TESTS, ("test_control_cancel_terminates_owned_native_picker_process", "test_session_expiry_terminates_owned_native_picker_process", "test_native_selected_path_flows_only_through_a1_candidate_preparation", "test_picker_stderr_and_raw_path_never_cross_safe_control_state"))
    require_markers(A3_RUNTIME_TESTS, ("test_start_restore_control_plane_uses_production_native_picker",))
    require_markers(A3_SMOKE, ("/usr/bin/osascript", "__CWOS_A3_OSASCRIPT_PROBE__", "PASS — C4-II-A3 NATIVE MACOS PICKER SMOKE PASSED"))


def check_a4_authorized_but_not_implemented() -> None:
    if "/backups/restore" in read(FRONTEND_ROUTES):
        fail("A4 route implementation leaked into A3 closure branch")
    tree = parse_python(RUNTIME)
    if tree is not None:
        browser_flow = function_unparse(tree, "open_runtime_browser")
        for forbidden in ("cw-control", "bootstrap", "session_token", "control_origin"):
            if forbidden in browser_flow:
                fail(f"A4 browser handoff leaked into closure branch: {forbidden!r}")
        for required in ("config.frontend_url", "config.backend_url", "webbrowser.open(target_url)"):
            if required not in browser_flow:
                fail(f"ordinary browser URL contract drifted: {required!r}")


def main() -> int:
    check_documentation_state()
    check_durable_authority_and_history()
    check_closed_a1_boundary()
    check_closed_a2_boundary()
    check_closed_a3_boundary()
    check_a4_authorized_but_not_implemented()

    if ERRORS:
        print("Documentation lifecycle consistency: FAIL")
        for error in ERRORS:
            print(f"- {error}")
        return 1

    print("Documentation lifecycle consistency: PASS")
    print(f"Checked {len(COMPACT_ACTIVE_FILES)} compact active files.")
    print(f"Verified {len(REQUIRED_HISTORY)} required history paths.")
    print(f"Verified {len(EXPECTED_HISTORY_BLOBS)} exact historical Git blob identities.")
    print("Verified PR #178 merged / C4-II-A3 exact-head closure evidence.")
    print("Verified C4-II-A3 is DONE and A4 is the only authorized next runtime slice.")
    print("Verified closed A1 non-destructive validation boundary remains intact.")
    print("Verified closed A2 loopback/session/security/replay boundary remains intact.")
    print("Verified closed A3 native-picker/process/privacy boundary remains intact.")
    print("Verified A4 is authorized but browser route/bootstrap/session implementation has not leaked into closure branch.")
    print("Verified A4 keeps browser presentation pathless and C4-II-B remains not authorized.")
    print("Verified ADR 0016 / ADR 0018 durable authority remains unchanged.")
    print("Verified maintained historical guidance and exact snapshots remain protected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
