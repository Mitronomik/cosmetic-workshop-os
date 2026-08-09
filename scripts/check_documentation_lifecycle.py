#!/usr/bin/env python3
"""Guard the current B1 implementation and all closed Restore boundaries."""

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
SOURCE_PROOF = P("launcher/restore/source_proof.py")
STAGING = P("launcher/restore/staging.py")
B1_TESTS = P("launcher/tests/test_restore_source_proof_binding.py")
A1 = P("launcher/restore/validation_session.py")
A1_SCRATCH = P("launcher/restore/validation_scratch.py")
A2_PROTOCOL = P("launcher/restore/control_protocol.py")
A2_SESSION = P("launcher/restore/control_session.py")
A2_PLANE = P("launcher/restore/control_plane.py")
A3_PICKER = P("launcher/restore/macos_picker.py")
A4_HANDOFF = P("launcher/restore/browser_handoff.py")
LAUNCHER_RUNTIME = P("launcher/runtime.py")
MAIN_TS = P("frontend/src/main.ts")
ROUTES = P("frontend/src/app-navigation-routes.ts")
BROWSER_CONTRACT = P("frontend/src/restore-control-contract.ts")
BROWSER_RUNTIME = P("frontend/src/restore-control-runtime.ts")
PRESENTATION = P("frontend/src/restore-control-presentation.ts")
ENTRY = P("frontend/src/restore-control-entry.ts")

EXPECTED_MAIN_BLOB = "ea98a76638bddcb5a92b9ba31941508f8a816d42"
EXPECTED_STAGING_BLOB = "3126d5b1e68e764c135739fad71915912481c493"
EXPECTED_A1_BLOB = "c8734ab60a576ecad53acd961571ddf2c14bdcf4"

ACTIVE = (README, PLAN, FOCUS, PROGRESS, HANDOFF_STATE, CHANGE_REQUESTS)
SUPPORTING = (CURRENT, A_SLICES, B_SLICES, PROFILE, DEPLOYMENT, PACKAGING)
CORE = (
    "PR #181 — MERGED — B1 AUTHORIZED",
    "C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN",
    "C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B — IN PROGRESS — SLICED",
    "C4-II-B1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
    "C4-II-B2 — PLANNED — NOT AUTHORIZED",
    "C4-II-B3 — PLANNED — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)
STALE = (
    "C4-II-B1 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-B — PLANNED — NOT AUTHORIZED",
    "C4-II-A4 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
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
            "d2549cd9be2b60c5aee2479050e05a6ad8530c6c",
            "beae1407af270ad1c800c308ea7907750430eb1d",
            EXPECTED_MAIN_BLOB,
            EXPECTED_STAGING_BLOB,
            "same `HeldSource` descriptor",
            "SOURCE_CHANGED",
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
            "B1 — Bind retained source proof into C4-I intake — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
            "ExpectedSourceProof",
            "ProofBoundRestoreRequest",
            "bind_expected_source_proof",
            "same `HeldSource`",
            "before `prepared`",
            "external",
            "B2 — Launcher destructive coordinator/control command — PLANNED — NOT AUTHORIZED",
            "B3 — Browser explicit destructive confirmation — PLANNED — NOT AUTHORIZED",
        ),
    )
    require(
        PROFILE,
        CORE
        + (
            "Implemented B1 seam — proof binding at C4-I intake",
            "ProofBoundRestoreRequest",
            "bind_expected_source_proof",
            "same `HeldSource` descriptor",
            "A path-only pre-check followed by a later re-open is forbidden",
        ),
    )

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
            "sessionStorage",
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


def check_closed_a_boundaries() -> None:
    if blob(MAIN_TS) != EXPECTED_MAIN_BLOB:
        fail(f"frontend/src/main.ts changed after A4 closure; expected blob {EXPECTED_MAIN_BLOB}")
    if blob(A1) != EXPECTED_A1_BLOB:
        fail(f"A1 validation-session implementation drifted; expected blob {EXPECTED_A1_BLOB}")

    for path in (A1, A1_SCRATCH, A2_PROTOCOL, A2_SESSION, A2_PLANE, A3_PICKER, A4_HANDOFF):
        no_destructive(path, {"webbrowser"} if path != A4_HANDOFF else {"subprocess"})

    require(A1, ("RestoreCandidatePreparationService", "RetainedSourceProof", "retained_proof"))
    require(A2_SESSION, ("BOOTSTRAP_RANDOM_BYTES = 32", "SESSION_RANDOM_BYTES = 32", "HEARTBEAT_INTERVAL_SECONDS = 15", "SESSION_EXPIRY_SECONDS = 60"))
    require(A2_PLANE, ("CONTROL_HOST = \"127.0.0.1\"", "/v1/bootstrap", "/v1/restore/select", "/v1/restore/cancel", "no-store"))
    require(A3_PICKER, ("OSASCRIPT_PATH = Path(\"/usr/bin/osascript\")", "choose file", "shell=False"))
    require(ROUTES, ("'/backups/restore': 'Резервные копии'",))
    require(BROWSER_CONTRACT, ("RESTORE_CONTROL_FRAGMENT_PREFIX = '#cw-control='", "RESTORE_SESSION_STORAGE_KEYS"))
    require(BROWSER_RUNTIME, ("credentials: 'omit'", "cache: 'no-store'", "Authorization", "command_seq"))
    require(PRESENTATION, ("Рабочие данные не изменены", "восстановление ещё не запускалось"))
    require(ENTRY, ("captureRestoreBootstrap", "window.sessionStorage", "MutationObserver"))

    browser = "\n".join(read(path) for path in (BROWSER_CONTRACT, BROWSER_RUNTIME, ENTRY, PRESENTATION))
    for marker in ("localStorage", "source_path", "execute_restore", '<input type="file"'):
        if marker in browser:
            fail(f"closed A4 browser authority drifted: {marker!r}")
    plane = read(A2_PLANE)
    for marker in ("/v1/restore/confirm", "/v1/restore/execute"):
        if marker in plane:
            fail(f"B2 command leaked before authorization: {marker}")


def check_b1_implementation() -> None:
    if blob(STAGING) != EXPECTED_STAGING_BLOB:
        fail(f"C4-I staging algorithm changed in B1; expected blob {EXPECTED_STAGING_BLOB}")

    require(
        CONTRACTS,
        (
            "SOURCE_CHANGED = \"source_changed\"",
            "class ExpectedSourceProof",
            "source_identity: \"SourceIdentity\"",
            "sha256: str",
            "class RestoreRequest",
            "selected_source: Path",
            "expected_source_proof = None",
            "class ProofBoundRestoreRequest(RestoreRequest)",
            "expected_source_proof: ExpectedSourceProof = field()",
            "Резервная копия изменилась после проверки.",
        ),
    )
    no_destructive(SOURCE_PROOF)
    require(
        SOURCE_PROOF,
        (
            "class SourceProofMismatchError",
            "def bind_expected_source_proof",
            "held.identity != expected.source_identity",
            "held.revalidate()",
            "held.assert_still_self_contained()",
            "held.digest()",
            "byte_count != held.size_bytes",
            "digest != expected.sha256",
        ),
    )

    tree = parse(ENGINE)
    if tree is not None:
        intake = function(tree, "_execute_authorized")
        order = [
            intake.find("open_selected_source"),
            intake.find("bind_expected_source_proof"),
            intake.find("_execute_with_source"),
        ]
        if any(pos < 0 for pos in order) or order != sorted(order):
            fail("B1 must bind proof after one source open and before _execute_with_source")
        for marker in ("expected_source_proof", "RestoreFailure.SOURCE_CHANGED"):
            if marker not in intake:
                fail(f"B1 engine intake missing marker: {marker!r}")

    require(
        B1_TESTS,
        (
            "ProofBoundRestoreRequest",
            "test_exact_a1_identity_and_digest_allow_existing_c4_i_flow",
            "test_proof_gate_and_stage_use_the_same_held_source_descriptor",
            "test_same_path_replaced_with_different_inode_is_refused_before_prepared",
            "test_same_inode_and_size_changed_bytes_are_refused_by_digest_proof",
            "test_sidecar_appearing_after_a1_validation_is_refused_before_prepared",
            "test_symlink_substitution_after_a1_validation_is_refused_before_prepared",
            "test_expected_digest_byte_count_mismatch_is_refused_before_prepared",
            "test_wrong_expected_sha_is_refused_without_source_or_database_mutation",
            "test_source_changed_result_exposes_no_absolute_path",
            "test_legacy_c4_i_request_without_expected_proof_is_behaviorally_unchanged",
        ),
    )


def main() -> int:
    check_docs()
    check_history()
    check_closed_a_boundaries()
    check_b1_implementation()

    if ERRORS:
        print("Documentation lifecycle consistency: FAIL")
        for error in ERRORS:
            print(f"- {error}")
        return 1

    print("Documentation lifecycle consistency: PASS")
    print(f"Checked {len(ACTIVE)} compact active files.")
    print(f"Verified {len(HISTORY)} required history paths.")
    print(f"Verified {len(HISTORY_BLOBS)} exact historical Git blob identities.")
    print("Verified PR #181 merged / B1-only authorization baseline.")
    print("Verified C4-II-A remains closed and frontend/A1 boundaries remain intact.")
    print("Verified C4-I staging.py remains byte-identical while B1 binds the same HeldSource before prepared.")
    print("Verified base RestoreRequest remains selected-source-only while ProofBoundRestoreRequest carries B1 evidence.")
    print("Verified ExpectedSourceProof and fixed SOURCE_CHANGED presentation contract.")
    print("Verified focused B1 substitution/digest/immutability/legacy test contracts are present.")
    print("Verified B2/B3 control/browser destructive authority remains not authorized.")
    print("Verified ADR 0016 / ADR 0018 durable authority remains unchanged.")
    print("Verified maintained historical guidance and exact snapshots remain protected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
