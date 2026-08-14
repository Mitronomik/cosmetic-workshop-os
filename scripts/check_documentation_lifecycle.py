#!/usr/bin/env python3
"""Guard closed Restore plus the CR-013 / D4-A implementation boundary.

D4-A, D4-B, D4-C and D4-D are lifecycle-closed. D4 is complete.
CR-014 authorizes D5 only as documentation + exact-package assisted-install rehearsal;
release/Phase-12/runtime expansion and Restore changes remain forbidden.

The complete pre-CR-013 checker is preserved byte-identically under
``docs/history/d4-pre-decision/``. Its 22 ``PINNED_BLOBS`` and 60
``HISTORY_BLOBS`` entries remain authoritative and are re-verified here so D4-A
cannot weaken previously accepted Restore/history integrity.
"""

from __future__ import annotations

import ast
import json
from hashlib import sha1
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
P = lambda value: ROOT / value

README = P("README.md")
DOCS_AGENTS = P("docs/AGENTS.md")
CURRENT = P("docs/current-lifecycle.md")
PLAN = P("docs/implementation-plan.md")
PACKAGING = P("docs/packaging.md")
DEPLOYMENT = P("docs/deployment.md")
UPDATE_GUIDE = P("docs/update-guide.md")
USER_INSTALL = P("docs/user-install.md")
REMOTE_INSTALL = P("docs/remote-install-checklist.md")
DOMAIN_D4 = P("docs/domain-model-d4-update-safety.md")
FOCUS = P("state/current-focus.md")
PROGRESS = P("state/progress.md")
HANDOFF = P("state/handoff.md")
CHANGE_REQUESTS = P("state/change-requests.md")
ADR16 = P("docs/decisions/0016-launcher-assisted-restore.md")
ADR18 = P("docs/decisions/0018-launcher-restore-interaction-and-validation-session.md")
ADR19 = P("docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md")
ADR20 = P("docs/decisions/0020-d4-update-safety-contract.md")
ADR21 = P("docs/decisions/0021-d5-remote-install-rehearsal-contract.md")
ADR22 = P("docs/decisions/0022-native-macos-application-lifecycle.md")
HISTORY_INDEX = P("docs/history/README.md")
LEGACY_CHECKER = P("docs/history/d4-pre-decision/check_documentation_lifecycle.py")
D4A_PRECLOSURE_MANIFEST = P("docs/history/d4-a-pre-closure/manifest.json")
D4A_PRECLOSURE_ABOUT = P("docs/history/d4-a-pre-closure/ABOUT.md")
D4B_PRECLOSURE_MANIFEST = P("docs/history/d4-b-pre-closure/manifest.json")
D4B_PRECLOSURE_ABOUT = P("docs/history/d4-b-pre-closure/ABOUT.md")
D4C_PRECLOSURE_MANIFEST = P("docs/history/d4-c-pre-closure/manifest.json")
D4C_PRECLOSURE_ABOUT = P("docs/history/d4-c-pre-closure/ABOUT.md")
D4D_PRECLOSURE_MANIFEST = P("docs/history/d4-d-pre-closure/manifest.json")
D4D_PRECLOSURE_ABOUT = P("docs/history/d4-d-pre-closure/ABOUT.md")
D5_PREDECISION_MANIFEST = P("docs/history/d5-pre-decision/manifest.json")
D5_PREDECISION_ABOUT = P("docs/history/d5-pre-decision/ABOUT.md")

VERSION_SOURCE = P("backend/VERSION")
VERSION_MODULE = P("backend/app/version.py")
STARTUP_COMPATIBILITY = P("backend/app/db/startup_compatibility.py")
STARTUP_SERVICE = P("backend/app/services/startup.py")
RUNTIME_IDENTITY = P("backend/app/services/runtime_identity.py")
SETTINGS_API = P("backend/app/api/settings.py")
BACKEND_PYPROJECT = P("backend/pyproject.toml")
PACKAGE_SCRIPT = P("scripts/package_macos.sh")
VERSION_VERIFIER = P("scripts/verify_product_version.py")
D4A_VERSION_TEST = P("backend/app/tests/test_d4_a_app_version.py")
D4A_PREFLIGHT_TEST = P("backend/app/tests/test_d4_a_startup_compatibility.py")
D4A_PACKAGE_TEST = P("macos_package/tests/test_d4_a_product_version_projection.py")
D4B_SERVICE = P("backend/app/services/update_safety.py")
D4B_TEST = P("backend/app/tests/test_d4_b_update_safety.py")
D4C_SETTINGS_SCHEMA = P("backend/app/schemas/settings.py")
D4C_SETTINGS_SERVICE = P("backend/app/services/settings.py")
D4C_FRONTEND = P("frontend/src/settings-update-status.ts")
D4C_BINDINGS = P("frontend/src/settings-tax-bindings.ts")
D4C_PACKAGE_ENTRYPOINT = P("macos_package/entrypoint.py")
D4C_USER_ALERT = P("macos_package/user_alert.py")
D4C_BACKEND_TEST = P("backend/app/tests/test_d4_c_update_status.py")
D4C_FRONTEND_TEST = P("frontend/test/settings-update-status.test.mjs")
D4C_PACKAGE_TEST = P("macos_package/tests/test_d4_c_update_failure_alerts.py")

DECISION_BASE = "dc2301f7d4e101ad0fba851325dae9274f02da0c"
CR013_MERGE_BASE = "4dbb83b9da3f0945bffde3187a69054305e01b28"
D4A_VERIFIED_PR_HEAD = "f294b15365fcf651790e2dc5638ed1551f616c3d"
D4A_MERGED_HEAD = "89dd69dc1958e622146e01869cc34d4cd2ec859e"
D4A_MERGED_RUN = "31699624984"
D4A_PRECLOSURE_MANIFEST_SHA = "7debfd4b40c1b32a00fe3417564fd97480f8f043"
D4B_VERIFIED_PR_HEAD = "8688fa3dba87205b4b4626ebab2902262fd4cd24"
D4B_MERGED_HEAD = "d60a3be993c76b59292cf27ee66bcbe856669fc4"
D4B_PR_HEAD_RUN = "31716610699"
D4B_MERGED_RUN = "31717705331"
D4B_PRECLOSURE_MANIFEST_SHA = "e3c1bd273e3eb2f248c8497fd36bf920be3def99"
D4C_IMPLEMENTATION_CODE_COMMIT = "adfe37a3f68a545635f173c22d4710eacde86e74"
D4C_VERIFIED_PR_HEAD = "ba577f1151e041c11019525862d9bb76eeb1404e"
D4C_MERGED_HEAD = "3d69df192b5bdff9c7df067d8c8fde40154ebac9"
D4C_PR_HEAD_RUN = "31747841343"
D4C_MERGED_RUN = "31749503618"
D4C_PRECLOSURE_MANIFEST_SHA = "22271c8327e3af235c52de88f6654a1f3808e54f"
D4D_VERIFIED_HEAD = "ec88b09193c8ed041e17daef3e3ffc0193d1b559"
D4D_FINAL_RUN = "31751386881"
D4D_PRECLOSURE_MANIFEST_SHA = "b403263c95c24aa02b884e97bc593d3d1aec9b58"
D5_DECISION_BASE = "a8a28672a6fd807cd59342a02a102b8e09128fff"
D5_PREDECISION_MANIFEST_SHA = "10376047c51c663c6d8042ae0983fea03c1b5a31"
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
    "D4 — Update safety — DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED",
    "D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED",
    "D4-D — Exact-package update verification and D4 lifecycle closure — DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED",
)

D5_STATUS = (
    "CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT",
    "D5 — Remote install checklist — BLOCKED — PRODUCT DEFECT CONFIRMED IN HUMAN REHEARSAL",
    "CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX",
    "D5 blocker fix — Native macOS application lifecycle — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "D5 verification — BLOCKED UNTIL FIX + FRESH EXACT-PACKAGE/HUMAN REHEARSAL",
    "PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015",
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

FORBIDDEN_ACTIVE = (
    "D5 — Remote install checklist — NOT AUTHORIZED BY CR-013",
    "No further implementation slice is authorized by CR-013",
    "Starting D5 requires a separate authorization decision/change request",
    "D5 remains unauthorized",
    "D5 is not authorized",
    "D5 — Remote install checklist — IMPLEMENTED",
    "D5 — Remote install checklist — DONE",
    "D5 — Remote install checklist — CLOSED",
    "D5 verification — PASSED",
    "D5 verification — COMPLETE",
    "PASS — D5 REMOTE INSTALL REHEARSAL PASSED",
    "PHASE 12 — MVP release preparation — AUTHORIZED",
    "PR28 — AUTHORIZED",
    "PR29 — AUTHORIZED",
    "Product release readiness — READY",
    "Product release readiness — CLAIMED",
    "Product release readiness — ACHIEVED",
    "auto-update — AUTHORIZED",
    "auto-update download — AUTHORIZED",
    "signing — AUTHORIZED",
    "notarization — AUTHORIZED",
    "DMG — AUTHORIZED",
    "PKG — AUTHORIZED",
    "App Store — AUTHORIZED",
    "release channels — AUTHORIZED",
    "GitHub Releases integration — AUTHORIZED",
    "public release hosting — AUTHORIZED",
    "MDM — AUTHORIZED",
    "remote-management integration — AUTHORIZED",
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
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == variable_name
            for target in node.targets
        ) and isinstance(node.value, ast.Dict):
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



def check_d4a_preclosure_snapshot() -> None:
    verify_blob(D4A_PRECLOSURE_MANIFEST, D4A_PRECLOSURE_MANIFEST_SHA, "D4-A pre-closure manifest")
    try:
        payload = json.loads(read(D4A_PRECLOSURE_MANIFEST))
    except json.JSONDecodeError as exc:
        ERRORS.append(f"D4-A pre-closure manifest does not parse: {exc}")
        return
    if payload.get("source_commit") != D4A_MERGED_HEAD:
        ERRORS.append("D4-A pre-closure manifest source commit changed")
    files = payload.get("files", {})
    expected_names = ('README.md', 'current-lifecycle.md', 'implementation-plan.md', 'packaging.md', 'deployment.md', 'update-guide.md', 'current-focus.md', 'progress.md', 'handoff.md', 'change-requests.md', 'check_documentation_lifecycle.py', 'history-README.md')
    if set(files) != set(expected_names):
        ERRORS.append(f"D4-A pre-closure manifest file set changed: {sorted(files)}")
    for name in expected_names:
        expected = files.get(name)
        if isinstance(expected, str):
            verify_blob(P(f"docs/history/d4-a-pre-closure/{name}"), expected, "D4-A pre-closure snapshot blob")
    require(D4A_PRECLOSURE_ABOUT, (D4A_MERGED_HEAD, D4A_VERIFIED_PR_HEAD, D4A_MERGED_RUN, "exact Git blob identity"))
    require(HISTORY_INDEX, ("d4-a-pre-closure/", D4A_MERGED_HEAD))

def check_d4b_preclosure_snapshot() -> None:
    verify_blob(D4B_PRECLOSURE_MANIFEST, D4B_PRECLOSURE_MANIFEST_SHA, "D4-B pre-closure manifest")
    try:
        payload = json.loads(read(D4B_PRECLOSURE_MANIFEST))
    except json.JSONDecodeError as exc:
        ERRORS.append(f"D4-B pre-closure manifest does not parse: {exc}")
        return
    if payload.get("source_commit") != D4B_MERGED_HEAD: ERRORS.append("D4-B pre-closure manifest source commit changed")
    if payload.get("verified_pr_head") != D4B_VERIFIED_PR_HEAD: ERRORS.append("D4-B pre-closure verified PR head changed")
    if payload.get("pr_head_verification_run") != D4B_PR_HEAD_RUN: ERRORS.append("D4-B pre-closure PR-head verification run changed")
    if payload.get("merged_head_verification_run") != D4B_MERGED_RUN: ERRORS.append("D4-B pre-closure merged-head verification run changed")
    files = payload.get("files", {})
    expected_names = ('README.md','current-lifecycle.md','implementation-plan.md','packaging.md','deployment.md','update-guide.md','current-focus.md','progress.md','handoff.md','change-requests.md','check_documentation_lifecycle.py','history-README.md')
    if set(files) != set(expected_names): ERRORS.append(f"D4-B pre-closure manifest file set changed: {sorted(files)}")
    for name in expected_names:
        expected=files.get(name)
        if isinstance(expected,str): verify_blob(P(f"docs/history/d4-b-pre-closure/{name}"), expected, "D4-B pre-closure snapshot blob")
    require(D4B_PRECLOSURE_ABOUT,(D4B_MERGED_HEAD,D4B_VERIFIED_PR_HEAD,D4B_PR_HEAD_RUN,D4B_MERGED_RUN,"`0` changed files","exact Git blob identity"))
    require(HISTORY_INDEX,("d4-b-pre-closure/",D4B_MERGED_HEAD))


def check_d4c_preclosure_snapshot() -> None:
    verify_blob(D4C_PRECLOSURE_MANIFEST, D4C_PRECLOSURE_MANIFEST_SHA, "D4-C pre-closure manifest")
    try:
        payload = json.loads(read(D4C_PRECLOSURE_MANIFEST))
    except json.JSONDecodeError as exc:
        ERRORS.append(f"D4-C pre-closure manifest does not parse: {exc}")
        return
    if payload.get("source_commit") != D4C_MERGED_HEAD: ERRORS.append("D4-C pre-closure manifest source commit changed")
    if payload.get("verified_pr_head") != D4C_VERIFIED_PR_HEAD: ERRORS.append("D4-C pre-closure verified PR head changed")
    if payload.get("pr_head_verification_run") != D4C_PR_HEAD_RUN: ERRORS.append("D4-C pre-closure PR-head verification run changed")
    if payload.get("merged_head_verification_run") != D4C_MERGED_RUN: ERRORS.append("D4-C pre-closure merged-head verification run changed")
    if payload.get("verified_head_to_merge_changed_files") != 0: ERRORS.append("D4-C verified-head to merge file count changed")
    files = payload.get("files", {})
    expected_names = ('README.md','current-lifecycle.md','implementation-plan.md','packaging.md','deployment.md','update-guide.md','current-focus.md','progress.md','handoff.md','change-requests.md','check_documentation_lifecycle.py','history-README.md')
    if set(files) != set(expected_names): ERRORS.append(f"D4-C pre-closure manifest file set changed: {sorted(files)}")
    for name in expected_names:
        expected = files.get(name)
        if isinstance(expected, str): verify_blob(P(f"docs/history/d4-c-pre-closure/{name}"), expected, "D4-C pre-closure snapshot blob")
    require(D4C_PRECLOSURE_ABOUT, (D4C_MERGED_HEAD, D4C_VERIFIED_PR_HEAD, D4C_PR_HEAD_RUN, D4C_MERGED_RUN, "`0` changed files", "exact Git blob identity"))
    require(HISTORY_INDEX, ("d4-c-pre-closure/", D4C_MERGED_HEAD))


def check_d4d_preclosure_snapshot() -> None:
    verify_blob(D4D_PRECLOSURE_MANIFEST, D4D_PRECLOSURE_MANIFEST_SHA, "D4-D pre-closure manifest")
    try: payload=json.loads(read(D4D_PRECLOSURE_MANIFEST))
    except json.JSONDecodeError as exc:
        ERRORS.append(f"D4-D pre-closure manifest does not parse: {exc}")
        return
    if payload.get("source_commit") != D4D_VERIFIED_HEAD: ERRORS.append("D4-D pre-closure source commit changed")
    if payload.get("d4d_final_verification_run") != D4D_FINAL_RUN: ERRORS.append("D4-D final verification run changed")
    files=payload.get("files", {})
    expected_names=('README.md','current-lifecycle.md','implementation-plan.md','packaging.md','deployment.md','update-guide.md','current-focus.md','progress.md','handoff.md','change-requests.md','check_documentation_lifecycle.py','history-README.md')
    if set(files) != set(expected_names): ERRORS.append(f"D4-D pre-closure manifest file set changed: {sorted(files)}")
    for name in expected_names:
        expected=files.get(name)
        if isinstance(expected,str): verify_blob(P(f"docs/history/d4-d-pre-closure/{name}"),expected,"D4-D pre-closure snapshot blob")
    require(D4D_PRECLOSURE_ABOUT,(D4D_VERIFIED_HEAD,D4D_FINAL_RUN,"PASS — FULL AUTOMATED SMOKE PASSED","exact Git blob identity"))
    require(HISTORY_INDEX,("d4-d-pre-closure/",D4D_VERIFIED_HEAD))


def check_d5_predecision_snapshot() -> None:
    verify_blob(D5_PREDECISION_MANIFEST, D5_PREDECISION_MANIFEST_SHA, "D5 pre-decision manifest")
    try:
        payload = json.loads(read(D5_PREDECISION_MANIFEST))
    except json.JSONDecodeError as exc:
        ERRORS.append(f"D5 pre-decision manifest does not parse: {exc}")
        return
    if payload.get("source_commit") != D5_DECISION_BASE:
        ERRORS.append("D5 pre-decision source commit changed")
    files = payload.get("files", {})
    expected_names = (
        "README.md", "current-lifecycle.md", "implementation-plan.md", "packaging.md",
        "deployment.md", "update-guide.md", "user-install.md", "remote-install-checklist.md",
        "docs-AGENTS.md", "decisions-AGENTS.md", "current-focus.md", "progress.md", "handoff.md",
        "change-requests.md", "check_documentation_lifecycle.py", "history-README.md",
    )
    if set(files) != set(expected_names):
        ERRORS.append(f"D5 pre-decision manifest file set changed: {sorted(files)}")
    for name in expected_names:
        expected = files.get(name)
        if isinstance(expected, str):
            verify_blob(P(f"docs/history/d5-pre-decision/{name}"), expected, "D5 pre-decision snapshot blob")
    require(D5_PREDECISION_ABOUT, (D5_DECISION_BASE, "exact Git blob identity"))
    require(HISTORY_INDEX, ("d5-pre-decision/", D5_DECISION_BASE))


def check_legacy_protections() -> None:
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
        require(path, D5_STATUS)
        forbid(path, FORBIDDEN_ACTIVE)
    for path in (README, CURRENT, FOCUS, PROGRESS, HANDOFF):
        require(path, CLOSED_TRUTH)
    require(CURRENT, ("ADR 0020", "ADR 0021", "ADR 0022", "D4-A closure truth", "D4-B closure truth", "D4-C closure truth", "D4-D closure truth", "D4 closure truth", "D5 decision truth", "D5 blocker truth", D4D_VERIFIED_HEAD, D4D_FINAL_RUN, "Restore remains closed"))
    require(PLAN, ("Normative D4 decision", "Normative D5 decision", "D4-A", "D4-B", "D4-C", "D4-D", "## D5 — Remote install checklist", "BLOCKED — PRODUCT DEFECT CONFIRMED", "## D5 blocker — Native macOS application lifecycle", "AUTHORIZED NEXT — NOT IMPLEMENTED"))
    require(PACKAGING, ("backend/VERSION", "package-runtime.json", "scripts/verify_product_version.py"))
    require(DEPLOYMENT, ("changes **no deployment topology**", "external user-data directory", "D4-B"))
    require(UPDATE_GUIDE, ("D4 Update Safety закрыт", "CR-014", "D5", "ещё не реализован/проверен", "старый пакет не является автоматическим откатом", "не включает автоматическое скачивание"))
    require(DOCS_AGENTS, ("ADR 0020", "docs/domain-model-d4-update-safety.md", "ADR 0021", "documentation + exact-package assisted-install rehearsal"))
    require(P("docs/decisions/AGENTS.md"), ("ADR 0021", "documentation + exact-package assisted-install rehearsal only", "not runtime changes"))
    require(FOCUS, ("Implement only the CR-015 native macOS application lifecycle blocker fix", "minimal native AppKit lifecycle wrapper", "Do not modify business logic, database semantics, Restore semantics, D4 update semantics"))
    require(USER_INSTALL, ("DRAFT SKELETON — D5 AUTHORIZED BUT NOT IMPLEMENTED OR VERIFIED", "Terminal/Git/Python/Node/Docker"))
    require(REMOTE_INSTALL, ("DRAFT SKELETON — D5 AUTHORIZED BUT NOT IMPLEMENTED OR VERIFIED", "ADR 0021"))


def check_adr20() -> None:
    require(ADR20, ADR20_SECTIONS + (
        DECISION_BASE,
        "one canonical build-time product-version source in the repository",
        "complete ordered `schema_migrations` lineage",
        "schema-newer-than-application",
        "STAGED MIGRATION + VERIFIED COMMIT",
        "launcher/startup-owned durable update metadata outside the working database",
        "previous package is **not a generic rollback mechanism after the database commit point**",
        "Only D4-A is authorized by this decision",
    ))
    forbid(ADR20, (
        "D4 — Update safety — IMPLEMENTED",
        "D4-B — Safe migration execution and durable UpdateLog — AUTHORIZED NEXT",
        "D5 — Remote install checklist — AUTHORIZED",
        "Product release readiness — READY",
    ))
    require(ADR16, ("before_restore", "replacement_intent", "recovery_blocked"))
    require(ADR18, ("127.0.0.1", "/backups/restore", "sessionStorage"))
    require(ADR19, ("D3 — macOS package MVP", "CR-012"))


def check_adr21() -> None:
    require(ADR21, (
        "ADR 0021 — D5 Remote Install Rehearsal contract",
        "Decision base: `a8a28672a6fd807cd59342a02a102b8e09128fff`",
        "documentation + exact-package assisted-install rehearsal stage",
        "clean Mac or clean macOS user profile",
        "Finder",
        "System Settings",
        "xattr",
        "spctl",
        "disable Gatekeeper globally",
        "exact Git commit SHA",
        "archive SHA-256 digest",
        "tested Mac hardware architecture",
        "exact macOS version",
        "synthetic test client",
        "synthetic test component",
        "synthetic test recipe",
        "PASS — D5 REMOTE INSTALL REHEARSAL PASSED",
        "INCONCLUSIVE — RUNNER",
        "INCONCLUSIVE — ENVIRONMENT",
        "does **not** equal product release readiness",
        "PHASE 12 — MVP release preparation",
        "Only D5 is authorized next",
    ))
    forbid(ADR21, (
        "Product release readiness — READY",
        "signing — AUTHORIZED",
        "notarization — AUTHORIZED",
        "DMG — AUTHORIZED",
        "App Store — AUTHORIZED",
        "auto-update — AUTHORIZED",
        "PHASE 12 — MVP release preparation — AUTHORIZED",
    ))


def check_adr22() -> None:
    require(ADR22, (
        "ADR 0022 — Native macOS application lifecycle blocker fix",
        "Status: **ACCEPTED — CR-015 BOUNDED FIX AUTHORIZED NEXT**",
        "Decision base: `c91e62930915da357a2f9c74b9a054fe98e9df14`",
        "FAIL — PRODUCT",
        "AppKit",
        "ordinary macOS Quit",
        "LaunchServices",
        "existing packaged bootstrap",
        "browser remains",
        "no business logic",
        "Objective-C",
        "no Electron",
        "fresh human clean-Mac/clean-profile rehearsal",
        "Only the **D5 blocker fix — Native macOS application lifecycle** is authorized next",
    ))
    forbid(ADR22, (
        "Product release readiness — READY",
        "signing — AUTHORIZED",
        "notarization — AUTHORIZED",
        "DMG — AUTHORIZED",
        "App Store — AUTHORIZED",
        "auto-update — AUTHORIZED",
        "PHASE 12 — MVP release preparation — AUTHORIZED",
    ))


def check_domain_clarification() -> None:
    require(DOMAIN_D4, (
        "AppSettings.app_version",
        "is **not** a mutable application-version authority",
        "AppSettings.schema_version",
        "is **not** a second numeric schema authority",
        "UpdateLog.backup_id",
        "outside the working database",
        "ordered `schema_migrations` lineage",
        "ADR 0020",
        "from_app_version",
        "currently recorded as `null`",
    ))


def check_d4a_implementation() -> None:
    version = read(VERSION_SOURCE)
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+\n", version):
        ERRORS.append("backend/VERSION is not one canonical major.minor.patch token")

    try:
        with BACKEND_PYPROJECT.open("rb") as handle:
            pyproject = tomllib.load(handle)
    except (FileNotFoundError, tomllib.TOMLDecodeError) as exc:
        ERRORS.append(f"backend/pyproject.toml cannot be checked: {exc}")
    else:
        project = pyproject.get("project", {})
        if "version" in project:
            ERRORS.append("backend pyproject retains an independent project.version literal")
        if "version" not in project.get("dynamic", []):
            ERRORS.append("backend pyproject does not declare dynamic version")
        projection = (
            pyproject.get("tool", {})
            .get("setuptools", {})
            .get("dynamic", {})
            .get("version", {})
            .get("file")
        )
        if projection != ["VERSION"]:
            ERRORS.append("backend pyproject dynamic version is not projected from VERSION")

    require(VERSION_MODULE, (
        "resolve_effective_app_version",
        "read_repository_app_version",
        "read_packaged_app_version",
        "package-runtime.json",
    ))
    require(STARTUP_COMPATIBILITY, (
        "inspect_startup_schema_compatibility",
        "mode=ro",
        "inspect_migration_lineage",
        "migration-history-unreadable",
        "supported_older",
    ))
    require(STARTUP_SERVICE, (
        "resolve_effective_app_version",
        "inspect_startup_schema_compatibility",
        "schema_compatibility.migrations_pending",
        "reconcile_interrupted_update",
        "execute_staged_update",
        "initialize_database(config)",
    ))
    forbid(STARTUP_SERVICE, ("pending_migration_ids",))
    require(RUNTIME_IDENTITY, ("get_runtime_settings_status", "resolve_effective_app_version"))
    require(SETTINGS_API, ("get_runtime_settings_status",))
    require(PACKAGE_SCRIPT, ("read_repository_app_version", "verify_product_version.py", "\"app_version\": \"$APP_VERSION\""))
    package_script_text = read(PACKAGE_SCRIPT)
    if re.search(r'APP_VERSION=[\"\'][0-9]+\.[0-9]+\.[0-9]+[\"\']', package_script_text):
        ERRORS.append("scripts/package_macos.sh contains an independent APP_VERSION semver literal")
    require(VERSION_VERIFIER, ("verify_product_version", "CFBundleShortVersionString", "package-runtime.json", "backend"))
    for test_file in (D4A_VERSION_TEST, D4A_PREFLIGHT_TEST, D4A_PACKAGE_TEST):
        if not test_file.is_file():
            ERRORS.append(f"missing D4-A focused test: {test_file.relative_to(ROOT)}")


def check_d4b_implementation() -> None:
    require(D4B_SERVICE, (
        "update-journal.json",
        "backup_sqlite_database",
        "_verify_before_migration_backup",
        "_create_consistent_stage_snapshot",
        "apply_migrations(DatabaseConfig(path=stage_path))",
        "_commit_verified_stage",
        "os.replace(stage_path, canonical_path)",
        "reconcile_interrupted_update",
        "interrupted-stage-identity-mismatch",
        "canonical-changed-during-staging",
        "post-commit-journal-write-failed",
        "from_app_version=None",
        "cannot prove the immediately previous package version",
        "stage_owned = False",
        "stage_owned = True",
    ))
    forbid(D4B_SERVICE, (
        "rolled_back",
        "shutil.copy",
        "shutil.copy2",
        "_previous_completed_app_version",
    ))
    if not D4B_TEST.is_file():
        ERRORS.append(f"missing D4-B focused test: {D4B_TEST.relative_to(ROOT)}")
    else:
        require(D4B_TEST, (
            "test_supported_older_user_startup_migrates_stage_then_commits",
            "test_staged_migration_failure_keeps_canonical_unchanged",
            "test_post_commit_journal_failure_reconciles_completed_next_launch",
            "test_tampered_interrupted_stage_identity_fails_closed_without_cleanup",
            "test_previous_completed_update_is_not_misreported_as_immediate_from_app_version",
            "test_preexisting_stage_collision_is_preserved",
            "test_canonical_sidecar_refuses_before_backup_or_stage",
        ))


def check_d4c_implementation() -> None:
    require(D4B_SERVICE, (
        "UpdateUserStatus", "read_user_update_status",
        "classify_update_failure_for_user", "error.committed",
        "SAFE_NO_UPDATE_STATUS", "SAFE_COMPLETED_UPDATE_STATUS",
    ))
    require(D4C_SETTINGS_SCHEMA, (
        "UpdateStatusSummary", "not_required", "completed",
        "attention_required", "to_app_version", "updated_at", "next_action",
    ))
    forbid(D4C_SETTINGS_SCHEMA, (
        "operation_id", "failure_category", "schema_identity",
        "stage_identity", "backup_identity",
    ))
    require(D4C_SETTINGS_SERVICE, (
        "read_user_update_status", "Можно продолжать работу.",
        "Ничего делать не нужно.", "Закройте приложение и откройте его снова.",
    ))
    require(D4C_PACKAGE_ENTRYPOINT, (
        "_classify_update_exception", "classify_update_failure_for_user",
        "EXIT_UPDATE_STOPPED_BEFORE_COMMIT", "EXIT_UPDATE_COMPLETION_UNCERTAIN",
        "D4-C classified startup-owned update failure",
    ))
    require(D4C_USER_ALERT, (
        "UPDATE_STOPPED_BEFORE_COMMIT", "UPDATE_COMPLETION_UNCERTAIN",
        "до замены рабочей базы данных",
        "Не удалось подтвердить завершение обновления данных",
        "Не пытайтесь вручную откатывать",
    ))
    require(D4C_FRONTEND, (
        "mountSettingsUpdateStatus", "fetch('/api/settings/status')",
        "Обновление завершено", "Нужно внимание", "Что делать:",
    ))
    forbid(D4C_FRONTEND, (
        "method: 'POST'", 'method: "POST"', "method: 'PUT'",
        "method: 'PATCH'", "method: 'DELETE'", "operation_id",
        "failure_category", "schema_identity", "stage_identity", "backup_identity",
    ))
    require(D4C_BINDINGS, ("mountSettingsUpdateStatus",))
    for path in (D4C_BACKEND_TEST, D4C_FRONTEND_TEST, D4C_PACKAGE_TEST):
        if not path.is_file():
            ERRORS.append(f"missing D4-C focused test: {path.relative_to(ROOT)}")
    require(D4C_BACKEND_TEST, (
        "test_no_journal_is_read_only_neutral_status",
        "test_failure_classifier_has_only_two_user_outcomes",
    ))
    require(D4C_FRONTEND_TEST, (
        "no update mutation", "caches the read for the UI session",
    ))
    require(D4C_PACKAGE_TEST, (
        "test_packaged_update_failures_use_fixed_d4c_catalog",
        "test_uncertain_message_never_suggests_manual_rollback",
    ))


def main() -> int:
    check_predecision_snapshot()
    check_legacy_protections()
    check_d4a_preclosure_snapshot()
    check_d4b_preclosure_snapshot()
    check_d4c_preclosure_snapshot()
    check_d4d_preclosure_snapshot()
    check_d5_predecision_snapshot()
    check_current_lifecycle()
    check_adr20()
    check_adr21()
    check_adr22()
    check_domain_clarification()
    check_d4a_implementation()
    check_d4b_implementation()
    check_d4c_implementation()

    if ERRORS:
        print("Documentation lifecycle consistency: FAIL")
        for error in ERRORS:
            print(f"- {error}")
        return 1

    print("Documentation lifecycle consistency: PASS")
    print("Verified exact pre-CR-013 lifecycle/state/checker snapshot.")
    print("Carried forward 22 closed Restore production blob protections.")
    print("Carried forward 60 protected lifecycle/history blob protections.")
    print("Verified D4-A is lifecycle-closed on the exact merged-head evidence.")
    print("Verified D4-B is lifecycle-closed on exact PR-head and merged-head Level-5 evidence.")
    print("Verified D4 is lifecycle-closed on final D4-D exact-package evidence.")
    print("Verified CR-014 D5 human rehearsal is blocked by a confirmed product lifecycle defect.")
    print("Verified CR-015 authorizes only the native macOS application lifecycle blocker fix.")
    print("Verified D5 closure, Phase 12 and product release readiness remain gated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
