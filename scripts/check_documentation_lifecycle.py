#!/usr/bin/env python3
"""Guard B2 closure, B3-only authorization, and all closed Restore boundaries."""

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

FRONTEND_MAIN = P("frontend/src/main.ts")
FRONTEND_CONTRACT = P("frontend/src/restore-control-contract.ts")

ACTIVE = (README, PLAN, FOCUS, PROGRESS, HANDOFF, CHANGE_REQUESTS)
SUPPORTING = (CURRENT, A_SLICES, B_SLICES, PROFILE, DEPLOYMENT, PACKAGING)

CORE = (
    "PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED",
    "PR #183 — MERGED — B2 AUTHORIZATION BASELINE",
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
    "C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B3 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-C — PLANNED — NOT AUTHORIZED",
    "C4-III — PLANNED — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)

COMPACT = (
    "PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED",
    "C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B3 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)

STALE = (
    "C4-II-B2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
    "C4-II-B2 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-B2 — PLANNED — NOT AUTHORIZED",
    "C4-II-B3 — PLANNED — NOT AUTHORIZED",
    "C4-II-B3 — DONE",
    "C4-II-B3 — IMPLEMENTED",
    "C4-II-C — AUTHORIZED NEXT",
    "C4-II-C — IN PROGRESS",
    "C4-III — AUTHORIZED NEXT",
    "C4-III — IN PROGRESS",
    "Restore — IMPLEMENTED",
    "Product release readiness — READY",
)

B1_REVIEWED_HEAD = "27726058af4f373ab65225ecf4d1a945f1c53067"
B1_MERGE_MAIN = "5e13b50f1918dacbf8d54066c9156942a9adb895"
B2_AUTH_REVIEWED_HEAD = "fa922f56c19a2dd33b6307ae0a197d476f91489b"
B2_AUTH_MERGE_MAIN = "4617b8c436eaa510fd545d863346595e2d808ea7"
B2_REVIEWED_HEAD = "1ae8bfcdf0f1f1798ce85eac0931925d029379c4"
B2_MERGE_MAIN = "266c50a77e5f353fa77701cb854629a99460667f"

# Exact accepted production/frontend boundaries on merge commit 266c50a...
PINNED_BLOBS = {
    # Closed B1/C4-I/A boundaries.
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

    # Newly closed B2 production boundary.
    P("launcher/restore/control_protocol.py"): "ab7240950d34228e0b81654a6c378c6cb77cb676",
    P("launcher/restore/control_session.py"): "aafa14b0a3ef126caddcb01e8429b5c26d80306c",
    P("launcher/restore/control_plane.py"): "b99a2ef2747cb4880465eb7b37e27cffbab18abc",
    P("launcher/restore/execution_coordinator.py"): "ea059358dd730969ccc8abcaaf6f7d4dfa5b3d51",
    P("launcher/runtime.py"): "7cca822944a335e03e196be6d9def8817267205e",

    # Pre-B3 frontend must stay byte-identical in this closure/authorization PR.
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
        CORE + (
            B1_REVIEWED_HEAD,
            B1_MERGE_MAIN,
            B2_AUTH_REVIEWED_HEAD,
            B2_AUTH_MERGE_MAIN,
            B2_REVIEWED_HEAD,
            B2_MERGE_MAIN,
            "Accepted B2 evidence",
            "Authorized successor — C4-II-B3",
            "request_id + command_seq + generation",
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
        CORE + (
            "B2 — launcher destructive coordinator/control command — DONE",
            B2_REVIEWED_HEAD,
            B2_MERGE_MAIN,
            "37 PASS",
            "2503/2503 PASS",
            "P0=0 / P1=0 / P2=0",
            "B3 — Browser explicit destructive confirmation — AUTHORIZED NEXT — NOT IMPLEMENTED",
            "POST /v1/restore/execute",
            "same request ID, command sequence and generation",
            "/v1/restore/confirm",
            "No launcher/backend changes are authorized",
        ),
    )

    require(
        PROFILE,
        CORE + (
            "B2 closure",
            B2_REVIEWED_HEAD,
            B2_MERGE_MAIN,
            "Authorized B3 browser confirmation contract",
            "Exact destructive replay",
            "same request ID, same command sequence and accepted generation",
        ),
    )

    require(
        PLAN,
        CORE + (
            "Current implementation window — C4-II-B3",
            "same request ID, command sequence and generation",
            "frontend-only",
        ),
    )

    require(
        DEPLOYMENT,
        COMPACT + (
            "same ephemeral control port",
            "B3 is frontend-only",
        ),
    )
    require(
        PACKAGING,
        COMPACT + (
            "B3 may change frontend assets only",
            "No source path, proof or digest",
        ),
    )

    for path in ACTIVE + SUPPORTING:
        text = norm(read(path))
        for stale in STALE:
            if norm(stale) in text:
                fail(f"{path.relative_to(ROOT)} retains stale/premature lifecycle phrase: {stale!r}")


def check_authority_decisions_and_history() -> None:
    require(ADR16, ("before_restore", "replacement_intent", "recovery_blocked", "selected source", "immutable"))
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
                f"closed B2/pre-B3 boundary changed: {path.relative_to(ROOT)} "
                f"expected blob {expected}, got {actual}"
            )


def check_b3_not_implemented() -> None:
    forbid(
        FRONTEND_CONTRACT,
        (
            "'restoring'",
            "'restore_completed'",
            "'restore_failed'",
            "'restore_blocked'",
            "| 'execute'",
        ),
    )
    forbid(
        FRONTEND_MAIN,
        (
            '"/v1/restore/execute"',
            "'/v1/restore/execute'",
            "restore_completed",
            "restore_blocked",
        ),
    )


def main() -> int:
    check_lifecycle_docs()
    check_authority_decisions_and_history()
    check_closed_boundaries()
    check_b3_not_implemented()

    if ERRORS:
        print("Documentation lifecycle consistency: FAIL")
        for error in ERRORS:
            print(f"- {error}")
        return 1

    print("Documentation lifecycle consistency: PASS")
    print(f"Checked {len(ACTIVE)} compact active files.")
    print(f"Verified {len(HISTORY)} required history paths.")
    print(f"Verified {len(HISTORY_BLOBS)} exact historical Git blob identities.")
    print(f"Verified {len(PINNED_BLOBS)} exact closed B1/C4-I/B2/pre-B3 Git blob identities.")
    print("Verified PR #184 reviewed head and merge/new-main evidence.")
    print("Verified C4-II-B2 is DONE — MERGED AND EXACT-HEAD VERIFIED.")
    print("Verified C4-II-B3 is the only AUTHORIZED NEXT implementation slice.")
    print("Verified B3 replay contract preserves request ID + command sequence + generation.")
    print("Verified no B3 frontend implementation leaked into this closure branch.")
    print("Verified C4-II-C/C4-III remain not authorized.")
    print("Verified Restore remains NOT IMPLEMENTED and release readiness is not claimed.")
    print("Verified ADR 0016 / ADR 0018 authority and protected history remain unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
