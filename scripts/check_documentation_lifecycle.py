#!/usr/bin/env python3
"""Check project lifecycle documentation for stale active instructions.

This is a docs-only consistency check. It does not inspect runtime behavior and
must not be presented as product smoke.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

CURRENT_PROFILE = ROOT / "docs/current-lifecycle.md"
CHANGE_REQUESTS = ROOT / "state/change-requests.md"

COMPACT_ACTIVE_FILES = (
    ROOT / "README.md",
    ROOT / "docs/implementation-plan.md",
    ROOT / "state/current-focus.md",
    ROOT / "state/progress.md",
    ROOT / "state/handoff.md",
    CHANGE_REQUESTS,
)

LEGACY_STATUS_FILES = (
    ROOT / "docs/architecture.md",
    ROOT / "docs/roadmap.md",
    ROOT / "docs/backup-and-restore.md",
)

REQUIRED_HISTORY = (
    ROOT / "docs/history/README.md",
    ROOT / "docs/history/project-timeline-through-pr170.md",
    ROOT / "docs/history/c4-i-implementation-and-audit-history.md",
    ROOT / "docs/history/implementation-plan/2026-08-06-pre-compaction.md",
    ROOT
    / "docs/history/state-snapshots/2026-08-06-c4-i-closure/current-focus.md",
    ROOT / "docs/history/state-snapshots/2026-08-06-c4-i-closure/progress.md",
    ROOT / "docs/history/state-snapshots/2026-08-06-c4-i-closure/handoff.md",
    ROOT / "docs/history/change-requests/2026-08-06-pre-compaction.md",
)

REQUIRED_CURRENT_MARKERS = (
    "C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "CR-011 — Launcher Restore interaction and validation-session boundary",
    "— AUTHORIZED — DECISION ONLY — NOT DECIDED",
    "C4-II-A — Launcher Restore source selection and validation presentation",
    "— PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Product release readiness — NOT CLAIMED",
)

STALE_ACTIVE_PHRASES = (
    "C4-I — IMPLEMENTED ON PR BRANCH",
    "C4-I — AUTHORIZED AFTER THE CR-010 DOCUMENTATION PR MERGES — NOT IMPLEMENTED",
    "C4 implementation — NOT STARTED",
    "implemented on a pull-request branch and not merged",
    "implemented on a pull-request branch and is not merged",
)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")
        return ""


def fail(message: str) -> None:
    ERRORS.append(message)


ERRORS: list[str] = []


def main() -> int:
    profile = read(CURRENT_PROFILE)

    for marker in REQUIRED_CURRENT_MARKERS:
        if marker not in profile:
            fail(f"current lifecycle profile is missing marker: {marker!r}")

    for path in LEGACY_STATUS_FILES:
        relative = path.relative_to(ROOT).as_posix()
        if f"`{relative}`" not in profile:
            fail(
                "legacy status file is not declared in the supersession map: "
                f"{relative}"
            )

    for path in REQUIRED_HISTORY:
        if not path.is_file():
            fail(f"missing preserved history: {path.relative_to(ROOT)}")

    for path in COMPACT_ACTIVE_FILES:
        text = read(path)
        for phrase in STALE_ACTIVE_PHRASES:
            if phrase.casefold() in text.casefold():
                fail(
                    f"stale lifecycle phrase remains in compact active file "
                    f"{path.relative_to(ROOT)}: {phrase!r}"
                )

    cr_text = read(CHANGE_REQUESTS)
    if "| CR-011 |" not in cr_text:
        fail("state/change-requests.md does not contain the CR-011 ledger row")
    if "authorized — decision only — not decided" not in cr_text.casefold():
        fail("CR-011 is not recorded as an undecided decision-only authorization")

    history_index = read(ROOT / "docs/history/README.md")
    unsafe_restore_example = "git restore --source=e699728"
    if unsafe_restore_example in history_index:
        fail(
            "history index recommends replacing active files with git restore; "
            "use git show or a detached worktree for inspection"
        )

    if ERRORS:
        print("Documentation lifecycle consistency: FAIL", file=sys.stderr)
        for error in ERRORS:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Documentation lifecycle consistency: PASS")
    print(f"Checked {len(COMPACT_ACTIVE_FILES)} compact active files.")
    print(f"Verified {len(REQUIRED_HISTORY)} preserved history paths.")
    print(
        "Legacy status prose is allowed only in the three explicitly "
        "superseded large reference documents."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
