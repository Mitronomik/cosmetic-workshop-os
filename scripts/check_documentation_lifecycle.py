#!/usr/bin/env python3
"""Check project lifecycle documentation for stale or contradictory guidance.

This is a docs-only consistency check. It does not inspect runtime behavior and
must not be presented as product smoke.
"""

from __future__ import annotations

from hashlib import sha1
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

CURRENT_PROFILE = ROOT / "docs/current-lifecycle.md"
DECISIONS_AGENTS = ROOT / "docs/decisions/AGENTS.md"
HISTORY_AGENTS = ROOT / "docs/history/AGENTS.md"
ADR_0016 = ROOT / "docs/decisions/0016-launcher-assisted-restore.md"
ADR_0017 = ROOT / "docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md"
ADR_0018 = ROOT / "docs/decisions/0018-launcher-restore-interaction-and-validation-session.md"
RESTORE_PROFILE = ROOT / "docs/restore-interaction-and-validation-session.md"
SLICE_PLAN = ROOT / "docs/c4-ii-a-implementation-slices.md"
CHANGE_REQUESTS = ROOT / "state/change-requests.md"
PACKAGING = ROOT / "docs/packaging.md"
DEPLOYMENT = ROOT / "docs/deployment.md"

COMPACT_ACTIVE_FILES = (
    ROOT / "README.md",
    ROOT / "docs/implementation-plan.md",
    ROOT / "state/current-focus.md",
    ROOT / "state/progress.md",
    ROOT / "state/handoff.md",
    CHANGE_REQUESTS,
)

SUPERSEDED_STATUS_FILES = (
    ADR_0016,
    ADR_0017,
    ROOT / "docs/architecture.md",
    ROOT / "docs/roadmap.md",
    ROOT / "docs/backup-and-restore.md",
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
    "PR #172 — MERGED — CR-011 ACCEPTED",
    "C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN",
    "C4-II-A — AUTHORIZED AS SLICED — NOT IMPLEMENTED",
    "C4-II-A1 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-A2 — PLANNED — BLOCKED BY A1 MERGE + EXACT-HEAD GATE",
    "C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE",
    "C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE",
    "C4-II-B — PLANNED — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)

PROFILE_ONLY_MARKERS = (
    "docs/decisions/0016-launcher-assisted-restore.md",
    "ADR 0017",
    "ADR 0018",
    "docs/c4-ii-a-implementation-slices.md",
    "PR #172 merge commit",
    "998596560db6780a677bdec363d1fd19db30c1b6",
    "Only A1 is the immediate successor after PR #173 merges",
    "Do not implement A1 on the unmerged PR #173 branch",
    "C4-II-B remains not authorized",
)

ADR_0018_REQUIRED_MARKERS = (
    "Option B",
    "Selected: Option B",
    "/backups/restore",
    "127.0.0.1",
    "/usr/bin/osascript",
    "Standard Additions `choose file`",
    "sessionStorage",
    "control_origin",
    "atomic compare-and-consume",
    "Cache-Control: no-store",
    "Mandatory concurrency model",
    "worker quiescence",
    "heartbeat interval: 15 seconds",
    "control-session expiry: 60 seconds",
    "command_seq",
    "consumes its command sequence",
    "0700",
    "prepare_restore_candidate",
    "SourceIdentity",
    "SHA-256",
    "ordinary backend remains running",
)

SLICE_PLAN_REQUIRED_MARKERS = (
    "C4-II-A — AUTHORIZED AS SLICED — NOT IMPLEMENTED",
    "C4-II-A1 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "C4-II-A2 — PLANNED — BLOCKED BY A1 MERGE + EXACT-HEAD GATE",
    "C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE",
    "C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE",
    "C4-II-B — PLANNED — NOT AUTHORIZED",
    "C4-II-A1 — Validation-session core",
    "C4-II-A2 — Exact-run launcher control plane",
    "C4-II-A3 — Native macOS picker integration",
    "C4-II-A4 — Browser Restore screen",
    "prepare_restore_candidate",
    "A1 must not implement HTTP control plane",
    "A2 must not implement real native picker",
    "A3 must not implement final browser Restore workspace",
    "A4 must not implement destructive Restore confirmation",
    "Each implementation slice starts from updated `main`",
    "P0=0/P1=0/P2=0 before merge",
    "C4-II-B remains separately not authorized",
)

RESTORE_PROFILE_REQUIRED_MARKERS = (
    "PR #172 — MERGED — CR-011 ACCEPTED",
    "C4-II-A — AUTHORIZED AS SLICED — NOT IMPLEMENTED",
    "C4-II-A1 — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "Restore control → launcher-owned 127.0.0.1:<ephemeral>",
    "/backups/restore",
    "/usr/bin/osascript",
    "sessionStorage",
    "control_origin",
    "atomic compare-and-consume",
    "worker quiescence",
    "heartbeat interval: 15 seconds",
    "control-session expiry: 60 seconds",
    "command_seq",
    "consumes its command sequence",
    "0700",
    "prepare_restore_candidate",
    "SourceIdentity",
    "SHA-256",
    "ordinary backend remains running",
    "A1 is the only immediate runtime successor",
    "C4-II-B/C4-II-C/C4-III",
)

STALE_COMPACT_ACTIVE_PHRASES = (
    "CR-011 — AUTHORIZED — DECISION ONLY — NOT DECIDED",
    "CR-011 — DECIDED — ADR 0018 ACCEPTED — NORMATIVE ON MAIN",
    "C4-II-A — PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED",
    "C4-II-A — PLANNED — NOT AUTHORIZED",
    "Finish and validate the **decision-only CR-011 pull request**",
    "Finish the CR-011 decision PR only",
    "After CR-011 merges, prepare a separate bounded C4-II-A authorization/task",
    "Do **not** begin C4-II-A by assumption",
    "Current work — CR-011",
)

MAINTAINED_HISTORY_GUIDANCE = (
    ROOT / "docs/history/AGENTS.md",
    ROOT / "docs/history/README.md",
    ROOT / "docs/history/c4-i-implementation-and-audit-history.md",
)

UNSAFE_EXECUTABLE_HISTORY_PATTERNS = (
    "--source=e6997281d2e0268ce54184d988c114bac71c35e2",
    "git restore --source=e699728",
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
    """Normalize presentation-only wrapping without weakening marker meaning."""

    return " ".join(text.split()).casefold()


def has_marker(text: str, marker: str) -> bool:
    return normalized(marker) in normalized(text)


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return sha1(header + data).hexdigest()


def require_markers(path: Path, markers: tuple[str, ...]) -> None:
    text = read(path)
    for marker in markers:
        if not has_marker(text, marker):
            fail(f"{path.relative_to(ROOT)} is missing marker: {marker!r}")


def main() -> int:
    profile = read(CURRENT_PROFILE)

    for marker in CORE_CURRENT_MARKERS + PROFILE_ONLY_MARKERS:
        if not has_marker(profile, marker):
            fail(f"current lifecycle profile is missing marker: {marker!r}")

    # Compact active control files must agree on post-PR-172 authorization and
    # must not keep the CR-011 decision branch or pre-authorization state current.
    for path in COMPACT_ACTIVE_FILES:
        text = read(path)
        require_markers(path, CORE_CURRENT_MARKERS)
        for phrase in STALE_COMPACT_ACTIVE_PHRASES:
            if has_marker(text, phrase):
                fail(
                    f"stale pre-PR-173 lifecycle phrase remains in compact active file "
                    f"{path.relative_to(ROOT)}: {phrase!r}"
                )

    # ADR scope/recency contract remains unchanged. ADR 0018 does not authorize
    # runtime by itself; PR #173's separate lifecycle/slice plan does.
    decisions_agents = read(DECISIONS_AGENTS)
    for marker in (
        "scope and recency",
        "ADR 0016 remains authoritative",
        "ADR 0017 supersedes the dated C4 implementation-status and authorization wording in ADR 0016",
        "ADR 0018 is newer for the exact CR-011 interaction/validation-session topic",
        "does **not** amend ADR 0016",
        "does **not** authorize C4-II-A runtime implementation",
    ):
        if not has_marker(decisions_agents, marker):
            fail(f"docs/decisions/AGENTS.md is missing ADR authority marker: {marker!r}")

    adr_0016_text = read(ADR_0016)
    if "C4-I — IMPLEMENTED ON PR BRANCH" in adr_0016_text:
        if "docs/decisions/0016-launcher-assisted-restore.md" not in profile:
            fail("ADR 0016 has dated lifecycle prose but is absent from supersession map")
        if not has_marker(profile, "ADR 0016 remains authoritative"):
            fail("current lifecycle does not preserve ADR 0016 durable authority")

    adr_0017_text = read(ADR_0017)
    if "CR-011" in adr_0017_text and "NOT DECIDED" in adr_0017_text:
        if not has_marker(profile, "ADR 0017 remains authoritative"):
            fail("current lifecycle does not preserve ADR 0017 C4-I closure authority")

    for path in SUPERSEDED_STATUS_FILES:
        relative = path.relative_to(ROOT).as_posix()
        if relative not in profile:
            fail(f"superseded status file is not declared in current lifecycle: {relative}")

    require_markers(ADR_0018, ADR_0018_REQUIRED_MARKERS)
    require_markers(SLICE_PLAN, SLICE_PLAN_REQUIRED_MARKERS)
    require_markers(RESTORE_PROFILE, RESTORE_PROFILE_REQUIRED_MARKERS)

    require_markers(
        PACKAGING,
        (
            "/usr/bin/osascript",
            "127.0.0.1",
            "C4-II-A1 — AUTHORIZED NEXT",
            "C4-II-A2 — BLOCKED BY A1 MERGE + EXACT-HEAD GATE",
            "C4-II-B destructive Restore remains not authorized",
            "Mac App Store sandbox compatibility",
        ),
    )
    require_markers(
        DEPLOYMENT,
        (
            "launcher-owned local control boundary",
            "127.0.0.1",
            "/usr/bin/osascript",
            "C4-II-A — AUTHORIZED AS SLICED — NOT IMPLEMENTED",
            "A1 may not implement the control plane, picker or frontend UI",
            "C4-II-B remains separately not authorized",
        ),
    )

    # Preserve searchable project memory byte-for-byte.
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

    for path in MAINTAINED_HISTORY_GUIDANCE:
        text = read(path)
        for pattern in UNSAFE_EXECUTABLE_HISTORY_PATTERNS:
            if pattern in text:
                fail(
                    f"maintained historical guidance contains an unsafe active-checkout "
                    f"restore recipe: {path.relative_to(ROOT)}"
                )

    history_policy = read(HISTORY_AGENTS)
    if "Do not use `git restore --source=<old-commit>`" not in history_policy:
        fail("docs/history/AGENTS.md does not prohibit active-checkout historical restore")

    cr_text = read(CHANGE_REQUESTS)
    if "| CR-011 |" not in cr_text:
        fail("state/change-requests.md does not contain the CR-011 ledger row")
    if not has_marker(cr_text, "accepted — ADR 0018 normative on main"):
        fail("CR-011 is not recorded as accepted on main")
    if not has_marker(cr_text, "PR #173 is **not** a new architecture/change request"):
        fail("PR #173 authorization is incorrectly missing its non-CR classification")
    if not has_marker(cr_text, "A1 is the only immediate runtime successor"):
        fail("ledger does not keep A1 as the only immediate successor")
    if not has_marker(cr_text, "C4-II-B remains **PLANNED — NOT AUTHORIZED**"):
        fail("ledger does not keep C4-II-B explicitly unauthorized")

    if ERRORS:
        print("Documentation lifecycle consistency: FAIL", file=sys.stderr)
        for error in ERRORS:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Documentation lifecycle consistency: PASS")
    print(f"Checked {len(COMPACT_ACTIVE_FILES)} compact active files.")
    print(f"Verified {len(REQUIRED_HISTORY)} required history paths.")
    print(f"Verified {len(EXPECTED_HISTORY_BLOBS)} exact historical Git blob identities.")
    print("Verified ADR 0016 / ADR 0017 / ADR 0018 scope-and-recency authority.")
    print("Verified PR #172 merged / CR-011 accepted baseline.")
    print("Verified sliced C4-II-A authorization and A1-only immediate successor.")
    print("Verified A2/A3/A4 predecessor merge + exact-head gates.")
    print("Verified C4-II-B remains separately not authorized.")
    print("Verified C4-II-A1 stays non-destructive and excludes control/picker/frontend scope.")
    print("Verified maintained historical guidance contains no executable old-commit restore recipe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
