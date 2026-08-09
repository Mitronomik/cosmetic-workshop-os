#!/usr/bin/env python3
"""Guard B1 closure, B2-only authorization, and the exact pre-B2 runtime boundary."""

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

ACTIVE = (README, PLAN, FOCUS, PROGRESS, HANDOFF, CHANGE_REQUESTS)
SUPPORTING = (CURRENT, A_SLICES, B_SLICES, PROFILE, DEPLOYMENT, PACKAGING)

CORE = (
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
    "C4-II-B2 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-B3 — PLANNED — NOT AUTHORIZED",
    "C4-II-C — PLANNED — NOT AUTHORIZED",
    "C4-III — PLANNED — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)

COMPACT_RESTORE_CORE = (
    "PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED",
    "C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B — IN PROGRESS — SLICED",
    "C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "C4-II-B2 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-B3 — PLANNED — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)

STALE = (
    "PR #181 — MERGED — B1 AUTHORIZED",
    "C4-II-B1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED",
    "C4-II-B1 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-B2 — PLANNED — NOT AUTHORIZED",
    "C4-II-B3 — AUTHORIZED NEXT",
    "C4-II-C — AUTHORIZED NEXT",
    "C4-II-C — IN PROGRESS",
    "C4-III — AUTHORIZED NEXT",
    "C4-III — IN PROGRESS",
)

B1_REVIEWED_HEAD = "27726058af4f373ab65225ecf4d1a945f1c53067"
B1_MERGE_MAIN = "5e13b50f1918dacbf8d54066c9156942a9adb895"

# Closure branches may document B2 but may not implement it. Pin every
# load-bearing B1/C4-I surface plus every closed A1/A2/A3/A4 launcher/runtime/
# frontend seam whose bytes must remain unchanged until B2 implementation begins.
# Any byte change in these protected pre-B2 surfaces fails this closure gate.
PINNED_BLOBS = {
    P("launcher/restore/contracts.py"): "1b4adf345b2470e7c50987570e7848012aa15a95",
    P("launcher/restore/engine.py"): "91eb99d14aa3dc70e7d6fb0d63cb03c6af7d255f",
    P("launcher/restore/source_proof.py"): "2339ee118d7ae85f792cb550c5a8ea1cc77f716c",
    P("launcher/restore/staging.py"): "3126d5b1e68e764c135739fad71915912481c493",
    P("launcher/restore/validation_session.py"): "c8734ab60a576ecad53acd961571ddf2c14bdcf4",
    P("launcher/restore/validation_scratch.py"): "6703052865d6e1d05dbfac14ea37fc47409d4da7",
    P("launcher/tests/test_restore_source_proof_binding.py"): "256ce4edc86d5060e056466bdeb35fb319269e33",
    P("launcher/restore/control_protocol.py"): "13ab63969cf419ff70ba93eaee750f946785046e",
    P("launcher/restore/control_session.py"): "617511e38ada4bf9fcbc5bc0922d9137135a85ea",
    P("launcher/restore/control_plane.py"): "e5d0227a05cd4c8a67480f63f1aade9401f1da32",
    P("launcher/restore/macos_picker.py"): "2bb2a048bb30866f9bf410da10a76537dbe09cdd",
    P("launcher/restore/browser_handoff.py"): "31aa42da893a551680091f9d7b97b3ef15422251",
    P("launcher/runtime.py"): "3f5381c3ad717d272deeb7617f2cfc2585c80c6c",
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
            "2480/2480",
            "external exact-head",
            "P0=0 / P1=0 / P2=0",
            "Only **C4-II-B2",
            "/v1/restore/execute",
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
            "B1 — Bind retained source proof into C4-I intake — DONE — MERGED AND EXACT-HEAD VERIFIED",
            "B2 — Launcher destructive coordinator/control command — AUTHORIZED NEXT",
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
            "maintenance lease",
            "B3 — Browser explicit destructive confirmation — PLANNED — NOT AUTHORIZED",
        ),
    )

    require(
        PROFILE,
        CORE
        + (
            "Authorized B2 coordinator seam",
            "POST /v1/restore/execute",
            "One-shot authority transfer",
            "Destructive work does not run in HTTP/session worker",
            "main launcher runtime loop",
            "same ephemeral port",
            "session expiry does not cancel C4-I",
            "Backend restart handoff",
            "restoring",
            "restore_completed",
            "restore_failed",
            "restore_blocked",
        ),
    )

    require(
        PLAN,
        CORE
        + (
            "Current implementation window — C4-II-B2",
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


def check_exact_pre_b2_runtime_boundary() -> None:
    for path, expected in PINNED_BLOBS.items():
        actual = blob(path)
        if actual and actual != expected:
            fail(
                f"B2 runtime implementation leaked into closure branch: "
                f"{path.relative_to(ROOT)} expected blob {expected}, got {actual}"
            )

    control_plane = P("launcher/restore/control_plane.py")
    control_session = P("launcher/restore/control_session.py")
    control_protocol = P("launcher/restore/control_protocol.py")
    runtime = P("launcher/runtime.py")
    frontend_contract = P("frontend/src/restore-control-contract.ts")

    forbid(control_plane, ("/v1/restore/execute", "/v1/restore/confirm"))
    forbid(
        control_session,
        ("RestoreExecutionIntent", "restore_completed", "restore_failed", "restore_blocked"),
    )
    forbid(
        control_protocol,
        (
            'RESTORING = "restoring"',
            "RESTORE_COMPLETED",
            "RESTORE_FAILED",
            "RESTORE_BLOCKED",
        ),
    )
    forbid(runtime, ("RestoreExecutionIntent",))
    forbid(
        frontend_contract,
        ("'restoring'", "'restore_completed'", "'restore_failed'", "'restore_blocked'", "'execute'"),
    )


def main() -> int:
    check_lifecycle_docs()
    check_authority_decisions_and_history()
    check_exact_pre_b2_runtime_boundary()

    if ERRORS:
        print("Documentation lifecycle consistency: FAIL")
        for error in ERRORS:
            print(f"- {error}")
        return 1

    print("Documentation lifecycle consistency: PASS")
    print(f"Checked {len(ACTIVE)} compact active files.")
    print(f"Verified {len(HISTORY)} required history paths.")
    print(f"Verified {len(HISTORY_BLOBS)} exact historical Git blob identities.")
    print("Verified PR #182 merged / C4-II-B1 exact-head closure evidence.")
    print("Verified B1 is DONE and B2 is the only authorized next implementation slice.")
    print("Verified exact /v1/restore/execute request, replay, one-shot generation/proof-transfer contract.")
    print("Verified destructive execution belongs to the launcher main runtime, never the HTTP/session worker.")
    print("Verified same control-plane lifetime and heartbeat/state availability across backend stop/restart.")
    print("Verified restart/result handoff and session-expiry non-cancellation semantics are documented.")
    print("Verified B3/C4-II-C/C4-III remain not authorized.")
    print(f"Verified {len(PINNED_BLOBS)} exact pre-B2 runtime/frontend Git blob identities.")
    print("Verified no B2 runtime implementation leaked into this closure branch.")
    print("Verified ADR 0016 / ADR 0018 durable authority remains unchanged.")
    print("Verified maintained historical guidance and exact snapshots remain protected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
