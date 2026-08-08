#!/usr/bin/env python3
"""Check C4-II-A3 implementation lifecycle and architecture boundaries."""

from __future__ import annotations

import ast
from hashlib import sha1
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

CURRENT_PROFILE = ROOT / "docs/current-lifecycle.md"
ADR_0016 = ROOT / "docs/decisions/0016-launcher-assisted-restore.md"
ADR_0018 = ROOT / "docs/decisions/0018-launcher-restore-interaction-and-validation-session.md"
RESTORE_PROFILE = ROOT / "docs/restore-interaction-and-validation-session.md"
SLICE_PLAN = ROOT / "docs/c4-ii-a-implementation-slices.md"
DEPLOYMENT = ROOT / "docs/deployment.md"
PACKAGING = ROOT / "docs/packaging.md"
README = ROOT / "README.md"
IMPLEMENTATION_PLAN = ROOT / "docs/implementation-plan.md"
CURRENT_FOCUS = ROOT / "state/current-focus.md"
PROGRESS = ROOT / "state/progress.md"
HANDOFF = ROOT / "state/handoff.md"
CHANGE_REQUESTS = ROOT / "state/change-requests.md"

A1_SESSION = ROOT / "launcher/restore/validation_session.py"
A1_SCRATCH = ROOT / "launcher/restore/validation_scratch.py"
A1_SMOKE = ROOT / "scripts/smoke_restore_validation_session.py"

A2_PROTOCOL = ROOT / "launcher/restore/control_protocol.py"
A2_SESSION = ROOT / "launcher/restore/control_session.py"
A2_PLANE = ROOT / "launcher/restore/control_plane.py"
A2_RUNTIME = ROOT / "launcher/runtime.py"
A2_SESSION_TESTS = ROOT / "launcher/tests/test_restore_control_session.py"
A2_PLANE_TESTS = ROOT / "launcher/tests/test_restore_control_plane.py"
A2_BOOTSTRAP_TESTS = ROOT / "launcher/tests/test_restore_control_bootstrap_concurrency.py"
A2_REJECTION_TESTS = ROOT / "launcher/tests/test_restore_control_rejection_order.py"
A2_HEADER_TESTS = ROOT / "launcher/tests/test_restore_control_header_cardinality.py"
A2_TOKEN_TESTS = ROOT / "launcher/tests/test_restore_control_tokens.py"
A2_RUNTIME_TESTS = ROOT / "launcher/tests/test_restore_control_runtime.py"
A2_ORIGIN_TESTS = ROOT / "launcher/tests/test_restore_control_runtime_origin.py"
A2_RACE_TESTS = ROOT / "launcher/tests/test_restore_control_stale_a1_authority.py"
A2_SMOKE = ROOT / "scripts/smoke_restore_control_plane.py"

A3_PICKER = ROOT / "launcher/restore/macos_picker.py"
A3_PICKER_TESTS = ROOT / "launcher/tests/test_restore_native_picker.py"
A3_SESSION_TESTS = ROOT / "launcher/tests/test_restore_native_picker_session.py"
A3_RUNTIME_TESTS = ROOT / "launcher/tests/test_restore_native_picker_runtime.py"
A3_SMOKE = ROOT / "scripts/smoke_restore_native_picker.py"

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
    RESTORE_PROFILE,
    SLICE_PLAN,
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
    ROOT / "docs/history/implementation-plan/2026-08-06-pre-compaction.md":
        "763a720ac7cc30c9eb870c5f24fa23aee75ea054",
    ROOT / "docs/history/state-snapshots/2026-08-06-c4-i-closure/current-focus.md":
        "3fcd869815a7559cc46f278b37ee06eae683dd75",
    ROOT / "docs/history/state-snapshots/2026-08-06-c4-i-closure/progress.md":
        "fcc0479d15cefa1672d01939418b9c37152559d7",
    ROOT / "docs/history/state-snapshots/2026-08-06-c4-i-closure/handoff.md":
        "e47f8872415ada073d5518c5bd24dace20ff5fe4",
    ROOT / "docs/history/change-requests/2026-08-06-pre-compaction.md":
        "85f284b0a08eba2a2f084672091cc9eedab261dc",
}

CORE_CURRENT_MARKERS = (
    "PR #176 — MERGED — C4-II-A2 EXACT-HEAD VERIFIED",
    "PR #177 — MERGED — A2 CLOSED / A3 AUTHORIZED",
    "C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN",
    "C4-II-A — IN PROGRESS — SLICED",
    "C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
    "C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE",
    "C4-II-B — PLANNED — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)

STALE_ACTIVE_PHRASES = (
    "C4-II-A3 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "A3 is the **only** authorized next runtime slice",
    "Production A2 still uses `UnavailableSourceSelectionAdapter`",
    "A3 may now add only",
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
    header = f"blob {len(data)}\0".encode("ascii")
    return sha1(header + data).hexdigest()


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
        if not isinstance(node, ast.Call):
            continue
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
    modules = imported_modules(tree)
    calls = called_names(tree)
    forbidden_modules = set(FORBIDDEN_DESTRUCTIVE_MODULES)
    forbidden_modules.update(extra_forbidden_modules or set())
    for module in sorted(forbidden_modules & modules):
        fail(f"{path.relative_to(ROOT)} imports forbidden scope: {module}")
    for name in sorted(FORBIDDEN_DESTRUCTIVE_CALLS & calls):
        fail(f"{path.relative_to(ROOT)} calls destructive boundary: {name}")


def check_documentation_state() -> None:
    for path in COMPACT_ACTIVE_FILES:
        require_markers(path, CORE_CURRENT_MARKERS)

    require_markers(
        CURRENT_PROFILE,
        CORE_CURRENT_MARKERS
        + (
            "d767b957cb3debae584709f2bbadafebd8dd6a9e",
            "e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263",
            "MacOSNativeSourceSelectionAdapter",
            "scripts/smoke_restore_native_picker.py",
            "No PASS is claimed until these run on the final published A3 head",
        ),
    )
    require_markers(
        SLICE_PLAN,
        (
            "C4-II-A3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
            "OSASCRIPT_PATH",
            "choose file",
            "error `-128`",
            "kill + reap",
            "A4 — Browser Restore screen and non-destructive E2E flow — BLOCKED",
            "C4-II-B — PLANNED — NOT AUTHORIZED",
        ),
    )
    require_markers(
        RESTORE_PROFILE,
        (
            "A3 native picker — CURRENT IMPLEMENTATION",
            "OSASCRIPT_PATH = Path(\"/usr/bin/osascript\")",
            "error `-128`",
            "A3→A4 browser seam",
            "C4-II-B remains separately not authorized",
        ),
    )
    require_markers(
        DEPLOYMENT,
        (
            "C4-II-A3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
            "/usr/bin/osascript",
            "no new dependency",
        ),
    )
    require_markers(
        PACKAGING,
        (
            "C4-II-A3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
            "/usr/bin/osascript",
            "Mac App Store sandbox compatibility is **not claimed**",
        ),
    )

    for path in COMPACT_ACTIVE_FILES + SUPPORTING_ACTIVE_FILES:
        text = read(path)
        for phrase in STALE_ACTIVE_PHRASES:
            if has_marker(text, phrase):
                fail(f"{path.relative_to(ROOT)} retains stale pre-A3-implementation phrase: {phrase!r}")


def check_durable_authority_and_history() -> None:
    require_markers(ADR_0016, ("before_restore", "replacement_intent", "recovery_blocked"))
    require_markers(
        ADR_0018,
        (
            "127.0.0.1",
            "/usr/bin/osascript",
            "choose file",
            "sessionStorage",
            "heartbeat interval: 15 seconds",
            "control-session expiry: 60 seconds",
        ),
    )
    for path in REQUIRED_HISTORY:
        if not path.exists():
            fail(f"missing required history path: {path.relative_to(ROOT)}")
    for path, expected in EXPECTED_HISTORY_BLOBS.items():
        if not path.exists():
            continue
        actual = git_blob_sha(path)
        if actual != expected:
            fail(
                f"protected history blob changed: {path.relative_to(ROOT)} "
                f"expected={expected} actual={actual}"
            )


def check_closed_a1_boundary() -> None:
    for path in (A1_SESSION, A1_SCRATCH):
        check_no_destructive_calls(
            path,
            extra_forbidden_modules={"http.server", "socket", "subprocess", "webbrowser"},
        )
    require_markers(
        A1_SESSION,
        (
            "RestoreCandidatePreparationService",
            "prepare_restore_candidate",
            "open_selected_source",
            "stage_source",
            "validate_staged_candidate",
            "SourceIdentity",
            "retained_proof",
            "MAX_DISPLAY_FILENAME_CHARS = 160",
        ),
    )
    require_markers(
        A1_SCRATCH,
        (
            "restore-validation",
            "PRIVATE_DIRECTORY_MODE = 0o700",
            "_ensure_default_private_root",
            "cleanup_interrupted_runs",
            "cleanup_session",
        ),
    )
    require_markers(
        A1_SMOKE,
        ("--expected-head", "PASS — C4-II-A1 VALIDATION-SESSION SMOKE PASSED"),
    )


def check_closed_a2_boundary() -> None:
    for path in (A2_PROTOCOL, A2_SESSION, A2_PLANE):
        check_no_destructive_calls(path, extra_forbidden_modules={"subprocess", "webbrowser"})

    require_markers(
        A2_PROTOCOL,
        (
            "SourceSelectionAdapter",
            "UnavailableSourceSelectionAdapter",
            "Closed A2 fail-closed/default adapter",
            "ControlStateSnapshot",
            "CommandReply",
        ),
    )
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
            "picker_unavailable",
            "command_sequence_stale",
            "command_sequence_future",
            "command_sequence_conflict",
            "guarantees stale A1 authority is gone before quiescence",
            "worker.join()",
        ),
    )
    require_markers(
        A2_PLANE,
        (
            "ThreadingHTTPServer",
            "CONTROL_HOST = \"127.0.0.1\"",
            "_ControlHTTPServer((CONTROL_HOST, 0)",
            "/v1/bootstrap",
            "/v1/state",
            "/v1/heartbeat",
            "/v1/restore/select",
            "/v1/restore/cancel",
            "Cache-Control",
            "no-store",
            "cookies_not_allowed",
            "REQUEST_ID_PATTERN",
            "invalid_request_schema",
        ),
    )
    plane_text = read(A2_PLANE)
    for browser_authority in ("source_path", "file_bytes", "upload_blob", "filesystem_handle"):
        if browser_authority in plane_text:
            fail(f"A2 HTTP boundary contains browser filesystem authority: {browser_authority!r}")

    require_markers(
        A2_SESSION_TESTS,
        (
            "test_bootstrap_is_one_use",
            "test_picker_unavailable_is_typed_and_pathless",
            "test_action_in_progress_consumes_its_valid_sequence",
            "test_heartbeat_and_state_remain_serviceable_while_worker_blocks",
            "test_expiry_invalidates_token_generation_and_retained_proof",
        ),
    )
    require_markers(
        A2_PLANE_TESTS,
        (
            "test_binds_exact_loopback_on_ephemeral_port_and_uses_no_store",
            "test_wrong_host_and_origin_do_not_consume_bootstrap",
            "test_preflight_is_narrow_and_never_wildcard",
            "test_malformed_path_bearing_select_does_not_consume_sequence",
        ),
    )
    require_markers(
        A2_BOOTSTRAP_TESTS,
        ("test_exact_same_bootstrap_capability_has_one_concurrent_winner", "threading.Barrier(2)"),
    )
    require_markers(A2_REJECTION_TESTS, ("test_wrong_host_origin_and_schema_do_not_consume_expected_command", "source_path"))
    require_markers(A2_HEADER_TESTS, ("test_missing_or_duplicate_host_origin_fail_before_bootstrap_consumption", "putheader"))
    require_markers(A2_TOKEN_TESTS, ("test_bootstrap_and_session_tokens_are_at_least_256_bit_and_run_scoped", "BOOTSTRAP_RANDOM_BYTES >= 32"))
    require_markers(A2_RUNTIME_TESTS, ("test_control_plane_starts_after_owned_backend_and_closes_before_backend", "#cw-control"))
    require_markers(A2_ORIGIN_TESTS, ("test_missing_configured_frontend_origin_fails_restore_control_closed",))
    require_markers(
        A2_RACE_TESTS,
        (
            "test_cancel_before_a1_begin_cannot_leave_resurrected_retained_proof",
            "test_expiry_before_a1_begin_cannot_leave_resurrected_retained_proof",
        ),
    )
    require_markers(A2_SMOKE, ("--expected-head", "PASS — C4-II-A2 RESTORE CONTROL-PLANE SMOKE PASSED"))


def check_a3_picker_boundary() -> None:
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
            "subprocess.DEVNULL",
            "subprocess.PIPE",
            "shell=False",
            "cancel_event.is_set()",
            "process.terminate()",
            "process.kill()",
            "process.communicate",
            "selected_path.is_absolute()",
            "SourceSelectionResult.unavailable()",
            "SourceSelectionResult.cancelled()",
            "SourceSelectionResult.selected(selected_path)",
        ),
    )
    picker_text = read(A3_PICKER)
    for forbidden in ("System Events", "shell=True", "/backups/restore", "execute_restore("):
        if forbidden in picker_text:
            fail(f"A3 picker contains forbidden marker: {forbidden!r}")

    runtime_tree = parse_python(A2_RUNTIME)
    if runtime_tree is not None:
        start_control = function_unparse(runtime_tree, "start_restore_control_plane")
        for required in (
            "MacOSNativeSourceSelectionAdapter",
            "picker_adapter=MacOSNativeSourceSelectionAdapter()",
            "config.frontend_url",
            "RestoreControlPlane",
        ):
            if required not in start_control:
                fail(f"production control-plane startup is missing A3 wiring: {required!r}")
        for forbidden in ("execute_restore", "before_restore", "sessionStorage", "cw-control"):
            if forbidden in start_control:
                fail(f"A3 runtime startup contains forbidden later/destructive marker: {forbidden!r}")

        runtime_flow = function_unparse(runtime_tree, "_run_locked_runtime")
        ordered = (
            "context.backend.start",
            "start_restore_control_plane",
            "open_runtime_browser",
            "control_plane.close",
            "context.backend.stop",
        )
        positions = [runtime_flow.find(marker) for marker in ordered]
        if any(position < 0 for position in positions) or positions != sorted(positions):
            fail("launcher runtime does not preserve backend→control→browser / control→backend ordering")

        browser_flow = function_unparse(runtime_tree, "open_runtime_browser")
        for forbidden in ("cw-control", "bootstrap", "session_token", "control_origin", "/backups/restore"):
            if forbidden in browser_flow:
                fail(f"production open_runtime_browser contains premature A4 marker: {forbidden!r}")
        for required in ("config.frontend_url", "config.backend_url", "webbrowser.open(target_url)"):
            if required not in browser_flow:
                fail(f"production open_runtime_browser drifted from ordinary URL contract: {required!r}")

    require_markers(
        A3_PICKER_TESTS,
        (
            "test_selected_path_uses_exact_owned_osascript_command",
            "test_user_cancel_is_typed_cancelled",
            "test_cancel_before_spawn_never_starts_child",
            "test_cancel_terminates_and_reaps_owned_picker_process",
            "test_terminate_timeout_kills_and_reaps_owned_picker_process",
            "test_non_macos_or_missing_exact_helper_is_typed_unavailable",
            "test_nonzero_or_non_absolute_output_is_internal_failure",
            "test_record_terminator_removal_preserves_filename_newline",
        ),
    )
    require_markers(
        A3_SESSION_TESTS,
        (
            "test_control_cancel_terminates_owned_native_picker_process",
            "test_session_expiry_terminates_owned_native_picker_process",
            "test_native_selected_path_flows_only_through_a1_candidate_preparation",
        ),
    )
    require_markers(
        A3_RUNTIME_TESTS,
        ("test_start_restore_control_plane_uses_production_native_picker", "MacOSNativeSourceSelectionAdapter"),
    )
    require_markers(
        A3_SMOKE,
        (
            "--expected-head",
            "/usr/bin/osascript",
            "__CWOS_A3_OSASCRIPT_PROBE__",
            "PASS — C4-II-A3 NATIVE MACOS PICKER SMOKE PASSED",
        ),
    )


def main() -> int:
    check_documentation_state()
    check_durable_authority_and_history()
    check_closed_a1_boundary()
    check_closed_a2_boundary()
    check_a3_picker_boundary()

    if ERRORS:
        print("Documentation lifecycle consistency: FAIL")
        for error in ERRORS:
            print(f"- {error}")
        return 1

    print("Documentation lifecycle consistency: PASS")
    print(f"Checked {len(COMPACT_ACTIVE_FILES)} compact active files.")
    print(f"Verified {len(REQUIRED_HISTORY)} required history paths.")
    print(f"Verified {len(EXPECTED_HISTORY_BLOBS)} exact historical Git blob identities.")
    print("Verified PR #177 merged / C4-II-A3 authorization baseline.")
    print("Verified C4-II-A3 current-changeset native picker boundary.")
    print("Verified exact /usr/bin/osascript + fixed choose-file script and no shell/System Events.")
    print("Verified cancel/expiry owned-child termination/quiescence test contracts.")
    print("Verified launcher-private path flows through closed A2 into A1 only.")
    print("Verified closed A1 and A2 boundaries remain intact.")
    print("Verified production browser navigation remains unchanged until A4.")
    print("Verified A4 predecessor gate and C4-II-B prohibition remain intact.")
    print("Verified ADR 0016 / ADR 0018 durable authority remains unchanged.")
    print("Verified maintained historical guidance and exact snapshots remain protected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
