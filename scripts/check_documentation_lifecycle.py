#!/usr/bin/env python3
"""Check post-A1 lifecycle closure and C4-II-A2 authorization consistency."""

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
    "C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN",
    "C4-II-A — IN PROGRESS — SLICED",
    "C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE",
    "C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE",
    "C4-II-B — PLANNED — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)

STALE_ACTIVE_PHRASES = (
    "C4-II-A1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
    "C4-II-A2 — PLANNED — BLOCKED BY A1 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE",
    "A2 remains blocked",
    "Finish A1 implementation review",
    "Verification still required",
    "Current work — A1 validation-session core",
)

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


def check_closed_a1_boundary() -> None:
    """Merged A1 must remain non-destructive and free of later-slice control scope."""

    for path in (A1_SESSION, A1_SCRATCH):
        tree = parse_python(path)
        if tree is None:
            continue
        modules = imported_modules(tree)
        calls = called_names(tree)

        forbidden_modules = {
            "http.server",
            "socket",
            "subprocess",
            "webbrowser",
            "launcher.restore.engine",
            "launcher.restore.state",
            "launcher.restore.safety_copy",
            "launcher.restore.replacement",
            "launcher.restore.recovery",
            "launcher.restore.phases",
        }
        for module in sorted(forbidden_modules & modules):
            fail(
                f"closed A1 module {path.relative_to(ROOT)} imports later/destructive scope: {module}"
            )

        forbidden_calls = {
            "execute_restore",
            "create_verified_safety_copy",
            "commit_replacement",
            "prepare_replacement_artifact",
            "quiesce_target_journal",
            "recover_incomplete_restore",
        }
        for name in sorted(forbidden_calls & calls):
            fail(
                f"closed A1 module {path.relative_to(ROOT)} calls destructive boundary: {name}"
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
            "INCONCLUSIVE — ENVIRONMENT",
            "FAIL — PRODUCT",
        ),
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
        "targeted A1 tests: 17 passed",
        "full backend + launcher regression: 2415 passed",
        "independent exact-head audit: P0=0 / P1=0 / P2=0",
        "A2 authorized boundary — exact-run launcher control plane",
        "picker_unavailable",
        "production product-browser launch URL remains unchanged in A2",
        "C4-II-B remains separately",
    ):
        if not has_marker(profile, marker):
            fail(f"current lifecycle profile is missing post-A1/A2 marker: {marker!r}")

    for path in COMPACT_ACTIVE_FILES:
        text = read(path)
        require_markers(path, CORE_CURRENT_MARKERS)
        for phrase in STALE_ACTIVE_PHRASES:
            if has_marker(text, phrase):
                fail(
                    f"stale pre-closure phrase remains in compact active file "
                    f"{path.relative_to(ROOT)}: {phrase!r}"
                )

    decisions_agents = read(DECISIONS_AGENTS)
    for marker in (
        "scope and recency",
        "ADR 0016 remains authoritative",
        "ADR 0018 is newer for the exact CR-011 interaction/validation-session topic",
        "does **not** amend ADR 0016",
        "does **not** authorize C4-II-A runtime implementation",
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
            "/backups/restore",
            "127.0.0.1",
            "/usr/bin/osascript",
            "sessionStorage",
            "control_origin",
            "atomic compare-and-consume",
            "Mandatory concurrency model",
            "worker quiescence",
            "command_seq",
            "consumes its command sequence",
            "0700",
            "prepare_restore_candidate",
            "SourceIdentity",
            "SHA-256",
            "ordinary backend remains running",
        ),
    )

    require_markers(
        SLICE_PLAN,
        (
            "C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
            "C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED",
            "picker_unavailable",
            "The browser may never provide source path",
            "production product-browser launch URL remains unchanged in A2",
            "A3 replaces the production `picker_unavailable` adapter",
            "/backups/restore",
            "C4-II-B — PLANNED — NOT AUTHORIZED",
        ),
    )

    require_markers(
        RESTORE_PROFILE,
        (
            "C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
            "C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED",
            "Restore control → launcher-owned 127.0.0.1:<ephemeral>",
            "restore-validation",
            "15-second heartbeat",
            "60 seconds",
            "command_seq",
            "picker_unavailable",
            "/usr/bin/osascript",
            "/backups/restore",
            "production product-browser launch URL remains unchanged",
        ),
    )

    require_markers(
        DEPLOYMENT,
        (
            "launcher-owned local control boundary",
            "C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
            "C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED",
            "picker_unavailable",
            "/usr/bin/osascript",
            "C4-II-B — PLANNED — NOT AUTHORIZED",
        ),
    )

    require_markers(
        PACKAGING,
        (
            "C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
            "C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED",
            "picker_unavailable",
            "/usr/bin/osascript",
            "Mac App Store sandbox compatibility",
            "C4-II-B destructive Restore remains not authorized",
        ),
    )

    check_closed_a1_boundary()

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
                    f"maintained historical guidance contains unsafe active-checkout restore recipe: "
                    f"{path.relative_to(ROOT)}"
                )

    cr_text = read(CHANGE_REQUESTS)
    if "| CR-011 |" not in cr_text:
        fail("state/change-requests.md does not contain CR-011")
    for marker in (
        "accepted — ADR 0018 normative on main",
        "PR #173 is **not** a new architecture/change request",
        "A1 is **DONE — MERGED AND EXACT-HEAD VERIFIED**",
        "This post-A1 closure is not a new CR",
        "A2 is **AUTHORIZED NEXT — NOT IMPLEMENTED**",
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
    print("Verified PR #174 merged / C4-II-A1 exact-head closure evidence.")
    print("Verified C4-II-A1 is DONE and A2 is the only authorized next runtime slice.")
    print("Verified A2 keeps picker_unavailable and no browser filesystem authority.")
    print("Verified A2 does not perform production browser fragment handoff before A4.")
    print("Verified A3/A4 predecessor gates and C4-II-B prohibition remain intact.")
    print("Verified merged A1 production boundary remains non-destructive.")
    print("Verified ADR 0016 / ADR 0018 durable authority remains unchanged.")
    print("Verified maintained historical guidance and exact snapshots remain protected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
