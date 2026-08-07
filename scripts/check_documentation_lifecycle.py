#!/usr/bin/env python3
"""Check C4-II-A2 implementation lifecycle and architecture boundaries."""

from __future__ import annotations

import ast
from hashlib import sha1
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

CURRENT_PROFILE = ROOT / "docs/current-lifecycle.md"
DECISIONS_AGENTS = ROOT / "docs/decisions/AGENTS.md"
ADR_0016 = ROOT / "docs/decisions/0016-launcher-assisted-restore.md"
ADR_0017 = ROOT / "docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md"
ADR_0018 = ROOT / "docs/decisions/0018-launcher-restore-interaction-and-validation-session.md"
RESTORE_PROFILE = ROOT / "docs/restore-interaction-and-validation-session.md"
SLICE_PLAN = ROOT / "docs/c4-ii-a-implementation-slices.md"
DEPLOYMENT = ROOT / "docs/deployment.md"
PACKAGING = ROOT / "docs/packaging.md"
CHANGE_REQUESTS = ROOT / "state/change-requests.md"
HISTORY_AGENTS = ROOT / "docs/history/AGENTS.md"

A1_SESSION = ROOT / "launcher/restore/validation_session.py"
A1_SCRATCH = ROOT / "launcher/restore/validation_scratch.py"
A1_TESTS = ROOT / "launcher/tests/test_restore_validation_session.py"
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
A2_SMOKE = ROOT / "scripts/smoke_restore_control_plane.py"

COMPACT_ACTIVE_FILES = (
    ROOT / "README.md",
    ROOT / "docs/implementation-plan.md",
    ROOT / "state/current-focus.md",
    ROOT / "state/progress.md",
    ROOT / "state/handoff.md",
    CHANGE_REQUESTS,
)

REQUIRED_HISTORY = (
    HISTORY_AGENTS,
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
    "PR #174 — MERGED — C4-II-A1 EXACT-HEAD VERIFIED",
    "PR #175 — MERGED — A1 CLOSED / A2 AUTHORIZED",
    "C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN",
    "C4-II-A — IN PROGRESS — SLICED",
    "C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
    "C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE",
    "C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE",
    "C4-II-B — PLANNED — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)

STALE_ACTIVE_PHRASES = (
    "C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "A2 runtime implementation begins only after",
    "merge post-A1 lifecycle closure",
    "Next runtime slice — A2",
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


def check_no_destructive_calls(path: Path, *, extra_forbidden_modules: set[str] | None = None) -> None:
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


def check_closed_a1_boundary() -> None:
    for path in (A1_SESSION, A1_SCRATCH):
        check_no_destructive_calls(
            path,
            extra_forbidden_modules={"http.server", "socket", "subprocess", "webbrowser"},
        )

    session_text = read(A1_SESSION)
    require_markers(
        A1_SESSION,
        (
            "RestoreCandidatePreparationService",
            "prepare_restore_candidate",
            "open_selected_source",
            "stage_source",
            "validate_staged_candidate",
            "SourceIdentity",
            "sha256",
            "retained_proof",
            "generation",
            "cancel",
            "MAX_DISPLAY_FILENAME_CHARS = 160",
        ),
    )
    for forbidden in (
        "ThreadingHTTPServer",
        "/usr/bin/osascript",
        "command_seq",
        "sessionStorage",
        "/backups/restore",
        "picker_unavailable",
    ):
        if forbidden in session_text:
            fail(f"closed A1 validation service contains later-slice marker: {forbidden!r}")

    require_markers(
        A1_SCRATCH,
        (
            "restore-validation",
            "VALIDATION_MARKER_VERSION",
            "PRIVATE_DIRECTORY_MODE = 0o700",
            "_ensure_default_private_root",
            "contains a symlink or non-directory",
            "cleanup_interrupted_runs",
            "cleanup_session",
        ),
    )
    require_markers(
        A1_TESTS,
        (
            "test_current_schema_is_accepted",
            "test_candidate_preparation_creates_no_restore_operation_safety_copy_audit_or_db_change",
            "test_cancel_during_validation_blocks_late_proof_publication",
            "test_default_scratch_refuses_symlinked_app_ancestry",
            "test_display_filename_is_bounded_and_removes_control_formatting",
        ),
    )
    require_markers(
        A1_SMOKE,
        (
            "--expected-head",
            "RestoreCandidatePreparationService",
            "PASS — C4-II-A1 VALIDATION-SESSION SMOKE PASSED",
        ),
    )


def check_a2_control_boundary() -> None:
    for path in (A2_PROTOCOL, A2_SESSION, A2_PLANE):
        check_no_destructive_calls(
            path,
            extra_forbidden_modules={"subprocess", "webbrowser"},
        )
        text = read(path)
        for forbidden in (
            "/usr/bin/osascript",
            "shell=True",
            "/backups/restore",
            "sessionStorage",
            "execute_restore(",
        ):
            if forbidden in text:
                fail(f"A2 production module {path.relative_to(ROOT)} contains later/destructive marker: {forbidden!r}")

    require_markers(
        A2_PROTOCOL,
        (
            "SourceSelectionAdapter",
            "UnavailableSourceSelectionAdapter",
            "UNAVAILABLE",
            "ControlStateSnapshot",
            "CommandReply",
            "ControlSessionError",
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
            "secrets.token_urlsafe",
            "_bootstrap_capability = \"\"",
            "_consume_command_locked",
            "action_in_progress",
            "picker_unavailable",
            "command_sequence_stale",
            "command_sequence_future",
            "command_sequence_conflict",
            "self._candidate_service.cancel()",
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
            "Access-Control-Allow-Origin",
            "cookies_not_allowed",
            "REQUEST_ID_PATTERN",
            "command_seq",
            "invalid_request_schema",
        ),
    )
    plane_text = read(A2_PLANE)
    for browser_authority in (
        "source_path",
        "file_bytes",
        "upload_blob",
        "filesystem_handle",
    ):
        if browser_authority in plane_text:
            fail(f"A2 HTTP boundary contains browser filesystem authority marker: {browser_authority!r}")

    runtime_tree = parse_python(A2_RUNTIME)
    if runtime_tree is not None:
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
        for forbidden in ("cw-control", "bootstrap", "session_token", "control_origin"):
            if forbidden in browser_flow:
                fail(f"production open_runtime_browser contains premature A4 handoff marker: {forbidden!r}")
        for required in ("config.frontend_url", "config.backend_url", "webbrowser.open(target_url)"):
            if required not in browser_flow:
                fail(f"production open_runtime_browser drifted from ordinary URL contract: {required!r}")

    require_markers(
        A2_SESSION_TESTS,
        (
            "test_bootstrap_is_one_use",
            "test_action_in_progress_consumes_its_valid_sequence",
            "test_heartbeat_and_state_remain_serviceable_while_worker_blocks",
            "test_cancel_prevents_late_selected_path_publication",
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
            "test_http_heartbeat_state_and_cancel_remain_responsive_while_worker_blocks",
        ),
    )
    require_markers(
        A2_BOOTSTRAP_TESTS,
        ("test_exact_same_bootstrap_capability_has_one_concurrent_winner", "threading.Barrier(2)"),
    )
    require_markers(
        A2_REJECTION_TESTS,
        ("test_wrong_host_origin_and_schema_do_not_consume_expected_command", "source_path"),
    )
    require_markers(
        A2_HEADER_TESTS,
        ("test_missing_or_duplicate_host_origin_fail_before_bootstrap_consumption", "putheader"),
    )
    require_markers(
        A2_TOKEN_TESTS,
        (
            "test_bootstrap_and_session_tokens_are_at_least_256_bit_and_run_scoped",
            "BOOTSTRAP_RANDOM_BYTES >= 32",
            "SESSION_RANDOM_BYTES >= 32",
        ),
    )
    require_markers(
        A2_RUNTIME_TESTS,
        (
            "test_control_plane_starts_after_owned_backend_and_closes_before_backend",
            "test_control_plane_failure_keeps_ordinary_product_available",
            "#cw-control",
        ),
    )
    require_markers(
        A2_SMOKE,
        (
            "--expected-head",
            "RestoreControlPlane",
            "/v1/bootstrap",
            "/v1/restore/select",
            "PASS — C4-II-A2 RESTORE CONTROL-PLANE SMOKE PASSED",
            "INCONCLUSIVE — ENVIRONMENT",
            "FAIL — PRODUCT",
        ),
    )


def check_history() -> None:
    for path in REQUIRED_HISTORY:
        if not path.is_file():
            fail(f"missing preserved history: {path.relative_to(ROOT)}")

    for path, expected_sha in EXPECTED_HISTORY_BLOBS.items():
        if not path.is_file():
            continue
        actual_sha = git_blob_sha(path)
        if actual_sha != expected_sha:
            fail(
                f"historical snapshot changed: {path.relative_to(ROOT)}; "
                f"expected blob {expected_sha}, got {actual_sha}"
            )

    history_policy = read(HISTORY_AGENTS)
    if "Do not use `git restore --source=<old-commit>`" not in history_policy:
        fail("docs/history/AGENTS.md does not prohibit active-checkout historical restore")

    for path in (
        ROOT / "docs/history/AGENTS.md",
        ROOT / "docs/history/README.md",
        ROOT / "docs/history/c4-i-implementation-and-audit-history.md",
    ):
        text = read(path)
        for unsafe in (
            "--source=e6997281d2e0268ce54184d988c114bac71c35e2",
            "git restore --source=e699728",
        ):
            if unsafe in text:
                fail(
                    "maintained historical guidance contains unsafe active-checkout "
                    f"restore recipe: {path.relative_to(ROOT)}"
                )


def main() -> int:
    profile = read(CURRENT_PROFILE)
    for marker in CORE_CURRENT_MARKERS:
        if not has_marker(profile, marker):
            fail(f"current lifecycle profile is missing marker: {marker!r}")

    for marker in (
        "C4-II-A1 / PR #174",
        "e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5",
        "504e776508c940554b3ee8659a201af21db8303c",
        "A1 closure / A2 authorization / PR #175",
        "b1a48d8f668fa984e3032f85c226f77e30d92e4e",
        "636645ece744752f6a753ae5a25a05297fd34e10",
        "A2 implemented boundary — exact-run launcher control plane",
        "UnavailableSourceSelectionAdapter",
        "picker_unavailable",
        "#cw-control",
        "C4-II-B remains",
    ):
        if not has_marker(profile, marker):
            fail(f"current lifecycle profile is missing A1/A2 marker: {marker!r}")

    for path in COMPACT_ACTIVE_FILES:
        text = read(path)
        require_markers(path, CORE_CURRENT_MARKERS)
        for phrase in STALE_ACTIVE_PHRASES:
            if has_marker(text, phrase):
                fail(f"stale pre-A2 phrase remains in {path.relative_to(ROOT)}: {phrase!r}")

    decisions_agents = read(DECISIONS_AGENTS)
    for marker in (
        "scope and recency",
        "ADR 0016 remains authoritative",
        "ADR 0018 is newer for the exact CR-011 interaction/validation-session topic",
        "does **not** amend ADR 0016",
    ):
        if not has_marker(decisions_agents, marker):
            fail(f"docs/decisions/AGENTS.md is missing ADR authority marker: {marker!r}")

    for path in (
        ADR_0016,
        ADR_0017,
        ROOT / "docs/architecture.md",
        ROOT / "docs/roadmap.md",
        ROOT / "docs/backup-and-restore.md",
    ):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in profile:
            fail(f"bounded superseded-status file is not mapped in current lifecycle: {relative}")

    require_markers(
        ADR_0018,
        (
            "Selected: Option B",
            "127.0.0.1",
            "atomic compare-and-consume",
            "Mandatory concurrency model",
            "worker quiescence",
            "command_seq",
            "consumes its command sequence",
            "prepare_restore_candidate",
            "/usr/bin/osascript",
            "/backups/restore",
            "sessionStorage",
            "ordinary backend remains running",
        ),
    )
    require_markers(
        SLICE_PLAN,
        (
            "C4-II-A2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
            "ThreadingHTTPServer",
            "picker_unavailable",
            "request_id",
            "command_seq",
            "production product-browser launch URL remains unchanged in A2",
            "A3 replaces the production `picker_unavailable` adapter",
            "/backups/restore",
            "C4-II-B — PLANNED — NOT AUTHORIZED",
        ),
    )
    require_markers(
        RESTORE_PROFILE,
        (
            "C4-II-A2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
            "ThreadingHTTPServer",
            "Restore control → launcher-owned 127.0.0.1:<ephemeral>",
            "15 seconds",
            "60 seconds",
            "command_seq",
            "UnavailableSourceSelectionAdapter",
            "picker_unavailable",
            "/usr/bin/osascript",
            "/backups/restore",
            "production product-browser launch URL remains unchanged",
        ),
    )
    require_markers(
        DEPLOYMENT,
        (
            "C4-II-A2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
            "launcher-owned local control boundary",
            "picker_unavailable",
            "/usr/bin/osascript",
            "#cw-control",
            "C4-II-B — PLANNED — NOT AUTHORIZED",
        ),
    )
    require_markers(
        PACKAGING,
        (
            "C4-II-A2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
            "picker_unavailable",
            "/usr/bin/osascript",
            "#cw-control",
            "Mac App Store sandbox compatibility",
            "C4-II-B destructive Restore remains not authorized",
        ),
    )

    check_closed_a1_boundary()
    check_a2_control_boundary()
    check_history()

    cr_text = read(CHANGE_REQUESTS)
    if "| CR-011 |" not in cr_text:
        fail("state/change-requests.md does not contain CR-011")
    for marker in (
        "accepted — ADR 0018 normative on main",
        "PR #173 is **not** a new architecture/change request",
        "A1 is **DONE — MERGED AND EXACT-HEAD VERIFIED**",
        "This post-A1 closure is not a new CR",
        "A2 is now **IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED**",
        "C4-II-B remains **PLANNED — NOT AUTHORIZED**",
    ):
        if not has_marker(cr_text, marker):
            fail(f"change-request ledger is missing marker: {marker!r}")

    if ERRORS:
        print("Documentation lifecycle consistency: FAIL", file=sys.stderr)
        for error in ERRORS:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Documentation lifecycle consistency: PASS")
    print(f"Checked {len(COMPACT_ACTIVE_FILES)} compact active files.")
    print(f"Verified {len(REQUIRED_HISTORY)} required history paths.")
    print(f"Verified {len(EXPECTED_HISTORY_BLOBS)} exact historical Git blob identities.")
    print("Verified PR #174 A1 closure and PR #175 A2 authorization baselines.")
    print("Verified C4-II-A2 current-changeset status and A3/A4 successor gates.")
    print("Verified A2 exact loopback/bootstrap/session/command-sequence boundary.")
    print("Verified A2 exact Host/Origin cardinality and token-size test contracts.")
    print("Verified A2 keeps picker_unavailable and no browser filesystem authority.")
    print("Verified production browser navigation remains unchanged until A4.")
    print("Verified launcher runtime owns control after backend proof and before backend stop.")
    print("Verified merged A1 boundary remains non-destructive and reusable by A2.")
    print("Verified C4-II-B remains separately not authorized.")
    print("Verified ADR 0016 / ADR 0018 durable authority remains unchanged.")
    print("Verified maintained historical guidance and exact snapshots remain protected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
