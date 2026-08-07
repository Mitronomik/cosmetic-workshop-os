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
    "PR #171 — MERGED",
    "C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "CR-011 — DECIDED — ADR 0018 ACCEPTED — NORMATIVE ON MAIN",
    "C4-II-A — PLANNED — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)

PROFILE_ONLY_MARKERS = (
    "docs/decisions/0016-launcher-assisted-restore.md",
    "docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md",
    "ADR 0017",
    "ADR 0018",
    "supersedes ADR 0017 only where ADR 0017 says CR-011 is still undecided",
    "launcher-owned loopback control plane",
    "/usr/bin/osascript",
    "Do not implement C4-II-A on this branch.",
    "separate bounded lifecycle/implementation task",
)

DECISION_REQUIRED_MARKERS = (
    "Option B",
    "Selected: Option B",
    "127.0.0.1",
    "ephemeral",
    "/usr/bin/osascript",
    "Standard Additions `choose file`",
    "sessionStorage",
    "URL fragment",
    "no wildcard origin",
    "heartbeat interval: 15 seconds",
    "control-session expiry: 60 seconds",
    "prepare_restore_candidate",
    "SourceIdentity",
    "SHA-256",
    "ordinary backend remains running",
    "C4-II-A — PLANNED — NOT AUTHORIZED",
    "C4-II-A runtime implementation",
)

RESTORE_PROFILE_REQUIRED_MARKERS = (
    "launcher-owned loopback control",
    "127.0.0.1",
    "/usr/bin/osascript",
    "sessionStorage",
    "15 seconds",
    "60 seconds",
    "prepare_restore_candidate",
    "SourceIdentity",
    "SHA-256",
    "C4-II-A — PLANNED — NOT AUTHORIZED",
)

STALE_COMPACT_ACTIVE_PHRASES = (
    "CR-011 — AUTHORIZED — DECISION ONLY — NOT DECIDED",
    "C4-II-A — PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED",
    "While PR #171 is open",
    "PR #171 is the current task",
    "Do not start CR-011 from the unmerged PR #171 branch",
    "Close PR #171 safely",
    "Current implementation window — close PR #171",
)

MAINTAINED_HISTORY_GUIDANCE = (
    ROOT / "docs/history/AGENTS.md",
    ROOT / "docs/history/README.md",
    ROOT / "docs/history/c4-i-implementation-and-audit-history.md",
)

# The unsafe historical recipe used the PR #170 merge SHA as a --source value.
# Generic `git restore --source=<old-commit>` may appear only as an explicit
# prohibition; an executable recipe with the real old SHA is never allowed.
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


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return sha1(header + data).hexdigest()


def require_markers(path: Path, markers: tuple[str, ...]) -> None:
    text = read(path)
    folded = text.casefold()
    for marker in markers:
        if marker.casefold() not in folded:
            fail(f"{path.relative_to(ROOT)} is missing marker: {marker!r}")


def main() -> int:
    profile = read(CURRENT_PROFILE)
    profile_folded = profile.casefold()

    for marker in CORE_CURRENT_MARKERS + PROFILE_ONLY_MARKERS:
        if marker.casefold() not in profile_folded:
            fail(f"current lifecycle profile is missing marker: {marker!r}")

    # Every compact active control file must agree on the post-PR-171 / CR-011
    # lifecycle and must not keep the former pre-merge action as current work.
    for path in COMPACT_ACTIVE_FILES:
        require_markers(path, CORE_CURRENT_MARKERS)
        text = read(path)
        folded = text.casefold()
        for phrase in STALE_COMPACT_ACTIVE_PHRASES:
            if phrase.casefold() in folded:
                fail(
                    f"stale pre-CR-011 lifecycle phrase remains in compact active file "
                    f"{path.relative_to(ROOT)}: {phrase!r}"
                )

    # ADR authority must remain explicitly bounded by scope and recency.
    decisions_agents = read(DECISIONS_AGENTS)
    for marker in (
        "scope and recency",
        "ADR 0016 remains authoritative",
        "ADR 0017 supersedes the dated C4 implementation-status and authorization wording in ADR 0016",
        "ADR 0018 is newer for the exact CR-011 interaction/validation-session topic",
        "does **not** amend ADR 0016",
        "does **not** authorize C4-II-A runtime implementation",
    ):
        if marker.casefold() not in decisions_agents.casefold():
            fail(f"docs/decisions/AGENTS.md is missing ADR authority marker: {marker!r}")

    # ADR 0016 intentionally retains branch-era lifecycle prose, so the current
    # profile must continue to list it in the bounded supersession map.
    adr_0016_text = read(ADR_0016)
    if "C4-I — IMPLEMENTED ON PR BRANCH" in adr_0016_text:
        if "docs/decisions/0016-launcher-assisted-restore.md" not in profile:
            fail("ADR 0016 has dated lifecycle prose but is absent from the supersession map")
        if "supersession remains bounded to lifecycle metadata only" not in profile_folded:
            fail("ADR 0016 lifecycle supersession is not explicitly bounded")

    # ADR 0017 intentionally remains accepted history for C4-I closure but its
    # pre-decision CR-011 status must now be explicitly bounded below ADR 0018.
    adr_0017_text = read(ADR_0017)
    if "CR-011" in adr_0017_text and "NOT DECIDED" in adr_0017_text:
        if "docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md" not in profile:
            fail("ADR 0017 has pre-decision CR-011 status but is absent from supersession map")
        if "ADR 0017 supersession is likewise bounded" not in profile:
            fail("ADR 0017 CR-011 supersession is not explicitly bounded")
        if "ADR 0017's C4-I closure facts" not in profile:
            fail("current lifecycle does not preserve ADR 0017 C4-I closure authority")

    for path in SUPERSEDED_STATUS_FILES:
        relative = path.relative_to(ROOT).as_posix()
        if relative not in profile:
            fail(f"superseded status file is not declared in current lifecycle: {relative}")

    # CR-011 must now be a real selected decision, not just a gate document.
    require_markers(ADR_0018, DECISION_REQUIRED_MARKERS)
    require_markers(RESTORE_PROFILE, RESTORE_PROFILE_REQUIRED_MARKERS)

    # The selected packaging/deployment consequences must be visible outside the
    # ADR so later packaging work does not silently invent another picker/control
    # architecture.
    require_markers(
        PACKAGING,
        (
            "/usr/bin/osascript",
            "127.0.0.1",
            "C4-II-A remains `PLANNED — NOT AUTHORIZED`",
            "Mac App Store sandbox compatibility",
        ),
    )
    require_markers(
        DEPLOYMENT,
        (
            "launcher-owned local control boundary",
            "127.0.0.1",
            "/usr/bin/osascript",
            "C4-II-A remains `PLANNED — NOT AUTHORIZED`",
        ),
    )

    # Preserve all searchable pre-compaction project memory byte-for-byte.
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

    # Maintained historical guidance may mention git restore only as a
    # prohibition; never retain an executable old-SHA recipe.
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

    # Current ledger must describe the decision while keeping implementation
    # authorization separate.
    cr_text = read(CHANGE_REQUESTS)
    cr_folded = cr_text.casefold()
    if "| CR-011 |" not in cr_text:
        fail("state/change-requests.md does not contain the CR-011 ledger row")
    if "decided — adr 0018 accepted" not in cr_folded:
        fail("CR-011 is not recorded as decided by ADR 0018")
    if "c4-ii-a remains not authorized" not in cr_folded:
        fail("CR-011 ledger does not keep C4-II-A explicitly unauthorized")
    if "separate bounded lifecycle/implementation task" not in profile_folded:
        fail("current lifecycle does not require a separate C4-II-A authorization task")

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
    print("Verified bounded ADR 0017 pre-decision CR-011 supersession.")
    print("Verified CR-011 selected loopback-control/picker/validation architecture.")
    print("Verified C4-II-A remains separately not authorized.")
    print("Verified maintained historical guidance contains no executable old-commit restore recipe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())