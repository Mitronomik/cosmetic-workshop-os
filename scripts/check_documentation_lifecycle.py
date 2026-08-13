#!/usr/bin/env python3
"""Guard the closed Restore lifecycle and the CR-013 / D4 authorization boundary.

CR-013 is a decision-only lifecycle change. It accepts ADR 0020, authorizes D4 as
an architecture programme, and authorizes only D4-A as the next runtime slice.
D4-B/C/D, D5 and release/distribution work remain gated.

The checker deliberately carries forward the exact protections from the checker
that closed C4-III. The complete pre-CR-013 checker is preserved byte-identically
under ``docs/history/d4-pre-decision/``. We parse its ``PINNED_BLOBS`` and
``HISTORY_BLOBS`` dictionaries and continue verifying every one of those exact
Git blob identities before checking the new D4 state. This prevents a lifecycle
compaction from weakening the already-accepted Restore/history integrity gate.
"""

from __future__ import annotations

import ast
from hashlib import sha1
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
P = lambda value: ROOT / value

README = P("README.md")
DOCS_AGENTS = P("docs/AGENTS.md")
CURRENT = P("docs/current-lifecycle.md")
PLAN = P("docs/implementation-plan.md")
PACKAGING = P("docs/packaging.md")
DEPLOYMENT = P("docs/deployment.md")
UPDATE_GUIDE = P("docs/update-guide.md")
DOMAIN_D4 = P("docs/domain-model-d4-update-safety.md")
FOCUS = P("state/current-focus.md")
PROGRESS = P("state/progress.md")
HANDOFF = P("state/handoff.md")
CHANGE_REQUESTS = P("state/change-requests.md")
ADR16 = P("docs/decisions/0016-launcher-assisted-restore.md")
ADR18 = P("docs/decisions/0018-launcher-restore-interaction-and-validation-session.md")
ADR19 = P("docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md")
ADR20 = P("docs/decisions/0020-d4-update-safety-contract.md")
HISTORY_INDEX = P("docs/history/README.md")
LEGACY_CHECKER = P("docs/history/d4-pre-decision/check_documentation_lifecycle.py")

DECISION_BASE = "dc2301f7d4e101ad0fba851325dae9274f02da0c"
LEGACY_CHECKER_SHA = "0d637269f802796098d5e6e911ad4d6a325ba990"

SNAPSHOT_BLOBS = {
    P("docs/history/d4-pre-decision/README.md"): "4e89b95a62d6b17b1a65d3dfeb8803c1b80733ee",
    P("docs/history/d4-pre-decision/current-lifecycle.md"): "b2fd84e338d7258a5aed49432a98e355e8da59fa",
    P("docs/history/d4-pre-decision/implementation-plan.md"): "2df67730f49a4f3136f8f694e7555ccf441eea1c",
    P("docs/history/d4-pre-decision/packaging.md"): "264024d4e24af3c37d01eb9daf3bad994e89376c",
    P("docs/history/d4-pre-decision/deployment.md"): "8b61f269b3dbaa8122b8134fb09a0812b63ba631",
    P("docs/history/d4-pre-decision/update-guide.md"): "fc293d9d8bab0a677ea83533e703132c5f6fed29",
    P("docs/history/d4-pre-decision/current-focus.md"): "60d9ba39af70b39f7484fa64343701b73aac34e7",
    P("docs/history/d4-pre-decision/progress.md"): "f00ecb180b8da92b2fe7a64eed880f1cdd0e3503",
    P("docs/history/d4-pre-decision/handoff.md"): "54396286426442c10cf4204a22ef847535ee49e0",
    P("docs/history/d4-pre-decision/change-requests.md"): "46a0c1909be13081711717da6ad5f8fcc7feea3b",
    P("docs/history/d4-pre-decision/check_documentation_lifecycle.py"): LEGACY_CHECKER_SHA,
    P("docs/history/d4-pre-decision/docs-AGENTS.md"): "5845a470ef94e925f06779498487797cf16b300a",
    P("docs/history/d4-pre-decision/history-README.md"): "fca8ff9cd6534b8c3b11cd6f358a44ab5dbad906",
}

D4_STATUS = (
    "CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT",
    "D4 — Update safety — AUTHORIZED — IMPLEMENTATION NOT STARTED",
    "D4-A — Version identity and compatibility preflight — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "D4-B — Safe migration execution and durable UpdateLog — PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED",
    "D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED",
    "D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED",
    "D5 — Remote install checklist — NOT AUTHORIZED BY CR-013",
    "Product release readiness — NOT CLAIMED",
)

CLOSED_TRUTH = (
    "C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED",
    "Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED",
    "D3 — macOS package MVP — IMPLEMENTED",
)

STATUS_SURFACES = (
    README,
    CURRENT,
    PLAN,
    PACKAGING,
    DEPLOYMENT,
    FOCUS,
    PROGRESS,
    HANDOFF,
    CHANGE_REQUESTS,
)

# These are authorization/lifecycle overclaims, not general semantic prose bans.
# "NOT AUTHORIZED" wording remains valid and is intentionally not caught.
FORBIDDEN_ACTIVE = (
    "D4 — Update safety — IMPLEMENTED",
    "D4 — Update safety — DONE",
    "D4 — Update safety — CLOSED",
    "D4-A — Version identity and compatibility preflight — IMPLEMENTED",
    "D4-A — Version identity and compatibility preflight — DONE",
    "D4-B — Safe migration execution and durable UpdateLog — AUTHORIZED NEXT",
    "D4-B — Safe migration execution and durable UpdateLog — IMPLEMENTED",
    "D4-C — User-facing update status and packaged failure UX — AUTHORIZED NEXT",
    "D4-C — User-facing update status and packaged failure UX — IMPLEMENTED",
    "D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT",
    "D4-D — Exact-package update verification and D4 lifecycle closure — IMPLEMENTED",
    "D5 — Remote install checklist — AUTHORIZED",
    "D5 — Remote install checklist — IMPLEMENTED",
    "Product release readiness — READY",
    "Product release readiness — CLAIMED",
    "Product release readiness — ACHIEVED",
    "auto-update — AUTHORIZED",
    "auto-update download — AUTHORIZED",
    "signing — AUTHORIZED",
    "notarization — AUTHORIZED",
    "DMG — AUTHORIZED",
    "App Store — AUTHORIZED",
    "release channels — AUTHORIZED",
    "GitHub Releases integration — AUTHORIZED",
    "Restore — NOT IMPLEMENTED",
    "Restore — IN PROGRESS",
    "Restore — AUTHORIZED NEXT",
)

ADR20_SECTIONS = (
    "## Context",
    "## Existing baseline",
    "## Problem",
    "## Decision",
    "## Version identity",
    "## Schema compatibility contract",
    "## Backup-before-migration contract",
    "## Migration failure safety",
    "## UpdateLog persistence",
    "## Update commit point",
    "## Interruption and repeated-launch behavior",
    "## User-facing success and failure truth",
    "## Manual package update contract",
    "## Downgrade behavior",
    "## Implementation slices",
    "## Explicit authorization boundary",
    "## Considered alternatives",
    "## Rejected alternatives",
    "## Consequences",
    "## Test contract",
    "## Stop conditions",
    "## Non-goals",
)

ADR20_CONTRACT = (
    DECISION_BASE,
    "one canonical build-time product-version source in the repository",
    "generated projections",
    "not authoritative",
    "complete ordered `schema_migrations` lineage",
    "schema-newer-than-application",
    "existing SQLite DB with no recognizable migration lineage",
    "SQLite Online Backup API",
    "Raw copying of the live `.sqlite` file",
    "STAGED MIGRATION + VERIFIED COMMIT",
    "transactionally consistent SQLite snapshot",
    "same filesystem",
    "atomic publication",
    "old canonical working database remains authoritative",
    "launcher/startup-owned durable update metadata outside the working database",
    "`started` is the durable non-terminal status",
    "not automatically equivalent to `failed`",
    "never trigger a blind destructive retry",
    "database update commit point",
    "later backend/listener/runtime failure is **not** recorded as \"migration failed\"",
    "previous package is **not a generic rollback mechanism after the database commit point**",
    "D4 implements no schema downgrade migrations",
    "Only D4-A is authorized by this decision",
    "Direct in-place migrations with backup only",
    "Second numeric schema-version field",
    "Database-only UpdateLog",
    "Reuse Restore as the update mechanism",
    "Staged migration before atomic commit",
    "Auto-updater/download mechanism",
)

ERRORS: list[str] = []


def norm(value: str) -> str:
    return " ".join(value.casefold().split())


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        ERRORS.append(f"missing file: {path.relative_to(ROOT)}")
        return ""


def require(path: Path, phrases: tuple[str, ...]) -> None:
    text = norm(read(path))
    for phrase in phrases:
        if norm(phrase) not in text:
            ERRORS.append(f"{path.relative_to(ROOT)} missing required truth: {phrase!r}")


def forbid(path: Path, phrases: tuple[str, ...]) -> None:
    text = norm(read(path))
    for phrase in phrases:
        if norm(phrase) in text:
            ERRORS.append(f"{path.relative_to(ROOT)} contains forbidden lifecycle overclaim: {phrase!r}")


def git_blob_sha(path: Path) -> str:
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        ERRORS.append(f"missing protected file: {path.relative_to(ROOT)}")
        return ""
    return sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def verify_blob(path: Path, expected: str, label: str) -> None:
    actual = git_blob_sha(path)
    if actual and actual != expected:
        ERRORS.append(
            f"{label} changed: {path.relative_to(ROOT)} expected {expected}, got {actual}"
        )


def _extract_legacy_blob_map(variable_name: str) -> dict[Path, str]:
    """Extract ``P('path'): 'sha'`` entries from the exact preserved old checker."""
    source = read(LEGACY_CHECKER)
    if not source:
        return {}
    try:
        tree = ast.parse(source, filename=str(LEGACY_CHECKER))
    except SyntaxError as exc:
        ERRORS.append(f"preserved legacy checker does not parse: {exc}")
        return {}

    assignment: ast.Dict | None = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == variable_name for target in node.targets):
            if isinstance(node.value, ast.Dict):
                assignment = node.value
            break
    if assignment is None:
        ERRORS.append(f"preserved legacy checker missing {variable_name}")
        return {}

    result: dict[Path, str] = {}
    for key_node, value_node in zip(assignment.keys, assignment.values, strict=True):
        if not (
            isinstance(key_node, ast.Call)
            and isinstance(key_node.func, ast.Name)
            and key_node.func.id == "P"
            and len(key_node.args) == 1
            and isinstance(key_node.args[0], ast.Constant)
            and isinstance(key_node.args[0].value, str)
            and isinstance(value_node, ast.Constant)
            and isinstance(value_node.value, str)
        ):
            ERRORS.append(f"unsupported entry in preserved {variable_name}")
            continue
        result[P(key_node.args[0].value)] = value_node.value
    return result


def check_predecision_snapshot() -> None:
    for path, expected in SNAPSHOT_BLOBS.items():
        verify_blob(path, expected, "pre-CR-013 snapshot blob")
    require(P("docs/history/d4-pre-decision/ABOUT.md"), (DECISION_BASE, "exact Git blob identity"))
    require(HISTORY_INDEX, ("d4-pre-decision/", DECISION_BASE))


def check_legacy_protections() -> None:
    # The preserved checker itself is pinned before trusting any dictionaries in it.
    verify_blob(LEGACY_CHECKER, LEGACY_CHECKER_SHA, "legacy lifecycle checker snapshot")
    pinned = _extract_legacy_blob_map("PINNED_BLOBS")
    history = _extract_legacy_blob_map("HISTORY_BLOBS")
    if len(pinned) != 22:
        ERRORS.append(f"legacy PINNED_BLOBS count changed: expected 22, got {len(pinned)}")
    if len(history) != 60:
        ERRORS.append(f"legacy HISTORY_BLOBS count changed: expected 60, got {len(history)}")
    for path, expected in pinned.items():
        verify_blob(path, expected, "closed Restore production blob")
    for path, expected in history.items():
        verify_blob(path, expected, "protected lifecycle/history blob")


def check_current_lifecycle() -> None:
    for path in STATUS_SURFACES:
        require(path, D4_STATUS)
        forbid(path, FORBIDDEN_ACTIVE)

    for path in (README, CURRENT, FOCUS, PROGRESS, HANDOFF):
        require(path, CLOSED_TRUTH)

    require(CURRENT, (DECISION_BASE, "ADR 0020", "Only D4-A may begin", "Restore remains closed"))
    require(PLAN, ("Normative D4 decision", "D4-A", "D4-B", "D4-C", "D4-D"))
    require(PACKAGING, ("manual package replacement", "is **not** a guaranteed rollback", "projections of that same source"))
    require(DEPLOYMENT, ("changes **no deployment topology**", "external user-data directory", "Only D4-A is authorized next"))
    require(UPDATE_GUIDE, ("реализация ещё не начата", "старый пакет не является автоматическим откатом", "не включает автоматическое скачивание"))
    require(DOCS_AGENTS, ("ADR 0020", "docs/domain-model-d4-update-safety.md"))


def check_adr20() -> None:
    require(ADR20, ADR20_SECTIONS + ADR20_CONTRACT + (
        "CR-013 — D4 Update Safety contract and bounded implementation authorization",
        "D4-A — Version identity and compatibility preflight",
        "D4-B — Safe migration execution and durable UpdateLog",
        "D4-C — User-facing update status and packaged failure UX",
        "D4-D — Exact-package update verification and lifecycle closure",
        "Product release readiness",
    ))
    # The accepted decision cannot silently claim it implemented the thing it only authorizes.
    forbid(ADR20, (
        "D4 — Update safety — IMPLEMENTED",
        "D4-A — Version identity and compatibility preflight — IMPLEMENTED",
        "D4-B — Safe migration execution and durable UpdateLog — AUTHORIZED NEXT",
        "D5 — Remote install checklist — AUTHORIZED",
        "Product release readiness — READY",
    ))
    require(ADR16, ("before_restore", "replacement_intent", "recovery_blocked"))
    require(ADR18, ("127.0.0.1", "/backups/restore", "sessionStorage"))
    require(ADR19, ("D3 — macOS package MVP", "CR-012"))


def check_domain_clarification() -> None:
    require(DOMAIN_D4, (
        "AppSettings.app_version",
        "is **not** a mutable application-version authority",
        "AppSettings.schema_version",
        "is **not** a second numeric schema authority",
        "UpdateLog.backup_id",
        "outside the working database",
        "started",
        "completed",
        "failed",
        "ordered `schema_migrations` lineage",
        "ADR 0020",
    ))


def main() -> int:
    check_predecision_snapshot()
    check_legacy_protections()
    check_current_lifecycle()
    check_adr20()
    check_domain_clarification()

    if ERRORS:
        print("Documentation lifecycle consistency: FAIL")
        for error in ERRORS:
            print(f"- {error}")
        return 1

    print("Documentation lifecycle consistency: PASS")
    print("Verified exact pre-CR-013 lifecycle/state/checker snapshot.")
    print("Carried forward 22 closed Restore production blob protections.")
    print("Carried forward 60 protected lifecycle/history blob protections.")
    print("Verified CR-013 accepted D4 architecture and authorizes only D4-A next.")
    print("Verified D4-B/C/D, D5 and product release readiness remain gated.")
    print("Verified ADR 0020 staged-migration, external UpdateLog and downgrade boundaries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
