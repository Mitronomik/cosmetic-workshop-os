#!/usr/bin/env python3
"""Guard the B2 implementation changeset and all closed Restore boundaries."""

from __future__ import annotations

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
HANDOFF = P("state/handoff.md")
CHANGE_REQUESTS = P("state/change-requests.md")
ADR16 = P("docs/decisions/0016-launcher-assisted-restore.md")
ADR18 = P("docs/decisions/0018-launcher-restore-interaction-and-validation-session.md")

CONTROL_PROTOCOL = P("launcher/restore/control_protocol.py")
CONTROL_SESSION = P("launcher/restore/control_session.py")
CONTROL_PLANE = P("launcher/restore/control_plane.py")
EXECUTION_COORDINATOR = P("launcher/restore/execution_coordinator.py")
RUNTIME = P("launcher/runtime.py")
B2_TESTS = P("launcher/tests/test_restore_execution_coordinator.py")
B2_C4I_TESTS = P("launcher/tests/test_restore_execution_coordinator_c4i.py")
B2_REPLAY_TESTS = P("launcher/tests/test_restore_execute_replay.py")
B2_RACE_TESTS = P("launcher/tests/test_restore_runtime_exit_seal.py")
B2_SAFETY_TESTS = P("launcher/tests/test_restore_execution_safety.py")
FRONTEND_CONTRACT = P("frontend/src/restore-control-contract.ts")

ACTIVE = (README, PLAN, FOCUS, PROGRESS, HANDOFF, CHANGE_REQUESTS)
SUPPORTING = (CURRENT, A_SLICES, B_SLICES, PROFILE, DEPLOYMENT, PACKAGING)

CORE = (
    "PR #183 — MERGED — B2 AUTHORIZED",
    "PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED",
    "C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN",
    "C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B — IN PROGRESS — SLICED",
    "C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
    "C4-II-B3 — PLANNED — NOT AUTHORIZED",
    "C4-II-C — PLANNED — NOT AUTHORIZED",
    "C4-III — PLANNED — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)

COMPACT_RESTORE_CORE = (
    "PR #183 — MERGED — B2 AUTHORIZED",
    "PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED",
    "C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B — IN PROGRESS — SLICED",
    "C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
    "C4-II-B3 — PLANNED — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)

STALE = (
    "PR #181 — MERGED — B1 AUTHORIZED",
    "C4-II-B1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
    "C4-II-B1 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-B2 — PLANNED — NOT AUTHORIZED",
    "C4-II-B2 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B3 — AUTHORIZED NEXT",
    "C4-II-B3 — IN PROGRESS",
    "C4-II-C — AUTHORIZED NEXT",
    "C4-II-C — IN PROGRESS",
    "C4-III — AUTHORIZED NEXT",
    "C4-III — IN PROGRESS",
)

B1_REVIEWED_HEAD = "27726058af4f373ab65225ecf4d1a945f1c53067"
B1_MERGE_MAIN = "5e13b50f1918dacbf8d54066c9156942a9adb895"
B2_AUTH_REVIEWED_HEAD = "fa922f56c19a2dd33b6307ae0a197d476f91489b"
B2_AUTH_MERGE_MAIN = "4617b8c436eaa510fd545d863346595e2d808ea7"

# B2 is authorized to change the control protocol/session/plane, launcher runtime,
# one focused execution coordinator and focused tests. Everything below is a
# closed A1/A3/A4/B1/C4-I or frontend boundary and must stay byte-identical.
PINNED_BLOBS = {
    P("launcher/restore/contracts.py"): "1b4adf345b2470e7c50987570e7848012aa15a95",
    P("launcher/restore/engine.py"): "91eb99d14aa3dc70e7d6fb0d63cb03c6af7d255f",
    P("launcher/restore/source_proof.py"): "2339ee118d7ae85f792cb550c5a8ea1cc77f716c",
    P("launcher/restore/staging.py"): "3126d5b1e68e764c135739fad71915912481c493",
    P("launcher/restore/validation_session.py"): "c8734ab60a576ecad53acd961571ddf2c14bdcf4",
    P("launcher/restore/validation_scratch.py"): "6703052865d6e1d05dbfac14ea37fc47409d4da7",
    P("launcher/restore/context.py"): "5795a6bd4339e77d60e27e282ad21d6df0f54364",
    P("launcher/restore/verification.py"): "1c3c25d0b0cf9b1e6ae4cb4931b56b3a9bf29772",
    P("launcher/restore/macos_picker.py"): "2bb2a048bb30866f9bf410da10a76537dbe09cdd",
    P("launcher/restore/browser_handoff.py"): "31aa42da893a551680091f9d7b97b3ef15422251",
    P("launcher/tests/test_restore_source_proof_binding.py"): "256ce4edc86d5060e056466bdeb35fb319269e33",
    P("frontend/src/main.ts"): "ea98a76638bddcb5a92b9ba31941508f8a816d42",
    P("frontend/src/app-navigation-routes.ts"): "cac0f380a6daf70cde21d8f5318c745e442e14e4",
    P("frontend/src/restore-control-contract.ts"): "227243fc9ceb3c833a474fc1f1d44e141cfe294c",
    P("frontend/src/restore-control-runtime.ts"): "c03d851d0c92278698683f8cbae4ed25a3de1392",
    P("frontend/src/restore-control-presentation.ts"): "9e9a08cd96278ccf6567533fc8d8c34e870dc184",
    P("frontend/src/restore-control-entry.ts"): "8248fef98932063c92729680627bd9db202acbf7",
}

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


def forbid(path: Path, markers: tuple[str, ...]) -> None:
    text = norm(read(path))
    for marker in markers:
        if norm(marker) in text:
            fail(f"{path.relative_to(ROOT)} contains forbidden marker: {marker!r}")


def blob(path: Path) -> str:
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        fail(f"missing pinned file: {path.relative_to(ROOT)}")
        return ""
    return sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def check_lifecycle_docs() -> None:
    for path in ACTIVE:
        require(path, CORE)

    require(
        CURRENT,
        CORE
        + (
            B1_REVIEWED_HEAD,
            B1_MERGE_MAIN,
            B2_AUTH_REVIEWED_HEAD,
            B2_AUTH_MERGE_MAIN,
            "B2 implementation changeset",
            "main launcher runtime",
            "same ephemeral port",
        ),
    )

    require(
        A_SLICES,
        (
            "CLOSED NORMATIVE IMPLEMENTATION PLAN",
            "C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED",
            "docs/c4-ii-b-implementation-slices.md",
        ),
    )

    require(
        B_SLICES,
        CORE
        + (
            "B2 — Launcher destructive coordinator/control command — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
            "POST /v1/restore/execute",
            '"request_id"',
            '"command_seq"',
            '"generation"',
            "RestoreExecutionIntent",
            "HTTP request returns; it does not call C4-I",
            "main launcher runtime",
            "same `127.0.0.1:<ephemeral>`",
            "session expiry invalidates browser authentication",
            "must not cancel",
            "restoring",
            "restore_completed",
            "restore_failed",
            "restore_blocked",
            "B3 — Browser explicit destructive confirmation — PLANNED — NOT AUTHORIZED",
        ),
    )

    require(
        PROFILE,
        CORE
        + (
            "Implemented B2 coordinator seam",
            "POST /v1/restore/execute",
            "One-shot authority transfer",
            "Destructive work does not run in HTTP/session worker",
            "main launcher runtime loop",
            "same ephemeral port",
            "session expiry does not cancel C4-I",
            "Backend restart handoff",
        ),
    )

    require(
        PLAN,
        CORE
        + (
            "Current implementation changeset — C4-II-B2",
            "request_id + command_seq + generation",
            "launcher-private RestoreExecutionIntent",
            "HTTP/session workers never call `execute_restore(...)`",
            "frontend remains byte-identical",
        ),
    )

    require(
        DEPLOYMENT,
        COMPACT_RESTORE_CORE
        + (
            "same ephemeral port",
            "main runtime owner path",
            "no new service, port, daemon, helper executable or dependency",
        ),
    )

    require(
        PACKAGING,
        COMPACT_RESTORE_CORE
        + (
            "same launcher process",
            "no new dependency",
            "Frontend assets remain byte-identical in B2",
        ),
    )

    for path in ACTIVE + SUPPORTING:
        text = norm(read(path))
        for stale in STALE:
            if norm(stale) in text:
                fail(f"{path.relative_to(ROOT)} retains stale lifecycle phrase: {stale!r}")


def check_authority_decisions_and_history() -> None:
    require(
        ADR16,
        (
            "before_restore",
            "replacement_intent",
            "recovery_blocked",
            "selected source",
            "immutable",
        ),
    )
    require(
        ADR18,
        (
            "127.0.0.1",
            "/backups/restore",
            "sessionStorage",
            "command_seq",
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


def check_closed_boundaries() -> None:
    for path, expected in PINNED_BLOBS.items():
        actual = blob(path)
        if actual and actual != expected:
            fail(
                f"closed pre-B2 boundary changed: {path.relative_to(ROOT)} "
                f"expected blob {expected}, got {actual}"
            )


def check_b2_implementation() -> None:
    require(
        CONTROL_PROTOCOL,
        (
            'RESTORING = "restoring"',
            'RESTORE_COMPLETED = "restore_completed"',
            'RESTORE_FAILED = "restore_failed"',
            'RESTORE_BLOCKED = "restore_blocked"',
        ),
    )

    require(
        CONTROL_PLANE,
        (
            '"/v1/restore/execute"',
            '_require_exact_keys(payload, {"request_id", "command_seq", "generation"})',
            "_parse_execute_payload",
            "self.plane.session.execute",
        ),
    )
    forbid(
        CONTROL_PLANE,
        (
            '"/v1/restore/confirm"',
            "from launcher.restore.engine import",
            "execute_restore(",
        ),
    )

    require(
        CONTROL_SESSION,
        (
            "RestoreExecutionIntent",
            "ExpectedSourceProof",
            'name="restore.execute"',
            'code="candidate_not_accepted"',
            'code="selection_generation_stale"',
            'code="restore_authority_missing"',
            'code="restore_in_progress"',
            'code="launcher_runtime_exiting"',
            "self._candidate_service.retained_proof",
            "self._candidate_service.invalidate()",
            "take_execution_intent",
            "take_execution_intent_or_seal_runtime_exit",
            "self._runtime_exit_sealed = True",
            "publish_execution_result",
            "self._execution_owner = None",
            "ControlViewState.RESTORING",
        ),
    )
    forbid(
        CONTROL_SESSION,
        (
            "from launcher.restore.engine import",
            "execute_restore(",
            "proof.generation ==",
            "== proof.generation",
        ),
    )

    require(
        EXECUTION_COORDINATOR,
        (
            "class RestoreExecutionIntent",
            "class RestoreExecutionSafetyError",
            "ProofBoundRestoreRequest",
            "execute_restore",
            "RetryableBackendStartError",
            "_require_maintenance_exclusion",
            "context.backend.start",
            "context.database_path",
            "ControlViewState.RESTORE_COMPLETED",
            "ControlViewState.RESTORE_FAILED",
            "ControlViewState.RESTORE_BLOCKED",
            'failure="backend_restart_failed"',
        ),
    )
    forbid(
        EXECUTION_COORDINATOR,
        (
            "threading.Thread",
            "ThreadingHTTPServer",
            '"/v1/restore/execute"',
            '"/v1/restore/confirm"',
        ),
    )

    require(
        RUNTIME,
        (
            "def _run_launcher_owner_loop",
            "take_execution_intent()",
            "take_execution_intent_or_seal_runtime_exit()",
            "execute_restore_intent(",
            "publish_execution_result",
            "RUNTIME_OWNER_POLL_SECONDS",
            "return _run_launcher_owner_loop(",
        ),
    )
    forbid(RUNTIME, ("return process.wait()",))

    require(
        B2_TESTS,
        (
            "test_execute_http_schema_is_exact",
            "test_execute_wrong_host_origin_and_auth_do_not_consume_sequence",
            "test_acceptance_transfers_current_private_proof_once_without_conflating_generations",
            "test_restoring_consumes_mutating_sequences_without_cancel_or_duplicate",
            "test_session_expiry_during_restoring_does_not_cancel_or_overwrite_result",
            "test_synchronous_coordinator_builds_proof_bound_request_and_restarts_canonical_backend",
            "test_restart_failure_preserves_result_truth_and_reacquires_exclusion",
            "test_retryable_verification_port_condition_starts_no_backend",
            "test_main_owner_loop_consumes_intent_before_observing_intentional_old_exit",
        ),
    )
    require(
        B2_C4I_TESTS,
        (
            "test_source_changed_real_c4i_refusal_restarts_without_working_db_mutation",
            "RestoreOperationStateStore",
            "workspace.safety_copies() == []",
        ),
    )
    require(
        B2_REPLAY_TESTS,
        (
            "test_execute_business_refusal_consumes_sequence_and_preserves_exact_replay",
            "command_sequence_conflict",
            "command_sequence_future",
            "command_sequence_stale",
        ),
    )
    require(
        B2_RACE_TESTS,
        (
            "test_late_execute_accepted_during_backend_exit_is_consumed_before_launcher_exit",
            "test_runtime_exit_seal_refuses_later_execute_without_queueing",
            "launcher_runtime_exiting",
        ),
    )
    require(
        B2_SAFETY_TESTS,
        (
            "test_unprovable_maintenance_exclusion_raises_launcher_safe_failure",
            "RestoreExecutionSafetyError",
        ),
    )

    forbid(
        FRONTEND_CONTRACT,
        (
            "'restoring'",
            "'restore_completed'",
            "'restore_failed'",
            "'restore_blocked'",
            "'execute'",
        ),
    )

    callers: list[str] = []
    launcher_root = P("launcher")
    for path in launcher_root.rglob("*.py"):
        if "tests" in path.parts:
            continue
        text = read(path)
        if "execute_restore_intent(" in text:
            callers.append(str(path.relative_to(ROOT)))
    expected_callers = {
        "launcher/runtime.py",
        "launcher/restore/execution_coordinator.py",
    }
    if set(callers) != expected_callers:
        fail(
            "execute_restore_intent must exist only at its definition and the main "
            f"launcher runtime call site; got {sorted(callers)}"
        )


def main() -> int:
    check_lifecycle_docs()
    check_authority_decisions_and_history()
    check_closed_boundaries()
    check_b2_implementation()

    if ERRORS:
        print("Documentation lifecycle consistency: FAIL")
        for error in ERRORS:
            print(f"- {error}")
        return 1

    print("Documentation lifecycle consistency: PASS")
    print(f"Checked {len(ACTIVE)} compact active files.")
    print(f"Verified {len(HISTORY)} required history paths.")
    print(f"Verified {len(HISTORY_BLOBS)} exact historical Git blob identities.")
    print("Verified PR #183 merged / B2 authorization evidence.")
    print("Verified B2 is implemented in this changeset but not lifecycle-closed.")
    print("Verified exact /v1/restore/execute schema and one-shot private authority transfer.")
    print("Verified HTTP/session code does not execute C4-I.")
    print("Verified destructive execution belongs to the main launcher runtime owner loop.")
    print("Verified accepted execute cannot be lost across an unexpected backend-exit race.")
    print("Verified unprovable maintenance exclusion fails closed through launcher cleanup.")
    print("Verified safe pathless B2 result states and restart/blocking handoff are present.")
    print("Verified B3/C4-II-C/C4-III remain not authorized.")
    print(f"Verified {len(PINNED_BLOBS)} exact closed B1/C4-I/A/frontend Git blob identities.")
    print("Verified frontend remains on the closed pre-B2 contract.")
    print("Verified ADR 0016 / ADR 0018 durable authority remains unchanged.")
    print("Verified maintained historical guidance and exact snapshots remain protected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
