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
CHANGE_REQUESTS = ROOT / "state/change-requests.md"

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
    "C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "CR-011 — AUTHORIZED — DECISION ONLY — NOT DECIDED",
    "C4-II-A — PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)

PROFILE_ONLY_MARKERS = (
    "docs/decisions/0016-launcher-assisted-restore.md",
    "ADR 0017",
    "supersedes only",
    "Do not start CR-011 from the unmerged PR #171 branch.",
    "After PR #171 is merged",
)

SEQUENCING_MARKERS = (
    "Do not start CR-011 from the unmerged PR #171 branch.",
    "PR #171",
)

STALE_ACTIVE_PHRASES = (
    "C4-I — IMPLEMENTED ON PR BRANCH",
    "C4-I — AUTHORIZED AFTER THE CR-010 DOCUMENTATION PR MERGES — NOT IMPLEMENTED",
    "C4 implementation — NOT STARTED",
    "implemented on a pull-request branch and not merged",
    "implemented on a pull-request branch and is not merged",
)

MAINTAINED_HISTORY_GUIDANCE = (
    ROOT / "docs/history/AGENTS.md",
    ROOT / "docs/history/README.md",
    ROOT / "docs/history/c4-i-implementation-and-audit-history.md",
)

UNSAFE_EXECUTABLE_HISTORY_PATTERNS = (
    "git restore \\\n  --source=",
    "git restore --source=e699",
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

    # Every compact current control file must carry the same core lifecycle and
    # must make PR #171 closure precede CR-011 work.
    for path in COMPACT_ACTIVE_FILES:
        require_markers(path, CORE_CURRENT_MARKERS)
        require_markers(path, SEQUENCING_MARKERS)

        text = read(path)
        for phrase in STALE_ACTIVE_PHRASES:
            if phrase.casefold() in text.casefold():
                fail(
                    f"stale lifecycle phrase remains in compact active file "
                    f"{path.relative_to(ROOT)}: {phrase!r}"
                )

    # ADR 0016 intentionally retains its original historical status table, but
    # current authority must explicitly scope that table below ADR 0017 without
    # revoking ADR 0016's durable Restore semantics.
    decisions_agents = read(DECISIONS_AGENTS)
    for marker in (
        "ADR 0017 supersedes the dated C4 implementation-status and authorization wording in ADR 0016",
        "ADR 0016 remains authoritative",
        "scope and recency",
    ):
        if marker.casefold() not in decisions_agents.casefold():
            fail(f"docs/decisions/AGENTS.md is missing ADR authority marker: {marker!r}")

    adr_0016_text = read(ADR_0016)
    if "C4-I — IMPLEMENTED ON PR BRANCH" in adr_0016_text:
        if "docs/decisions/0016-launcher-assisted-restore.md" not in profile:
            fail("ADR 0016 has dated lifecycle prose but is absent from the supersession map")
        if "supersedes only" not in profile_folded:
            fail("ADR 0016 lifecycle supersession is not explicitly bounded")

    for path in SUPERSEDED_STATUS_FILES:
        relative = path.relative_to(ROOT).as_posix()
        if relative not in profile:
            fail(f"superseded status file is not declared in current lifecycle: {relative}")

    for path in REQUIRED_HISTORY:
        if not path.is_file():
            fail(f"missing preserved history: {path.relative_to(ROOT)}")

    # Exact pre-compaction snapshots must remain byte-for-byte identical to the
    # original Git blobs even if the active docs are later compacted again.
    for path, expected_sha in EXPECTED_HISTORY_BLOBS.items():
        if not path.is_file():
            continue
        actual_sha = git_blob_sha(path)
        if actual_sha != expected_sha:
            fail(
                f"historical snapshot changed: {path.relative_to(ROOT)}; "
                f"expected blob {expected_sha}, got {actual_sha}"
            )

    # Maintained history guidance may mention git restore only as a prohibition;
    # it must not contain an executable old-commit restore recipe.
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
    if "authorized — decision only — not decided" not in cr_text.casefold():
        fail("CR-011 is not recorded as an undecided decision-only authorization")
    if "successor after pr #171 merge" not in cr_text.casefold():
        fail("CR-011 ledger row does not state that it is a successor after PR #171 merge")

    if ERRORS:
        print("Documentation lifecycle consistency: FAIL", file=sys.stderr)
        for error in ERRORS:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Documentation lifecycle consistency: PASS")
    print(f"Checked {len(COMPACT_ACTIVE_FILES)} compact active files.")
    print(f"Verified {len(REQUIRED_HISTORY)} required history paths.")
    print(f"Verified {len(EXPECTED_HISTORY_BLOBS)} exact historical Git blob identities.")
    print("Verified ADR 0016 / ADR 0017 scope-and-recency authority.")
    print("Verified PR #171 closure precedes CR-011 branch creation.")
    print("Verified maintained historical guidance contains no executable old-commit restore recipe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())