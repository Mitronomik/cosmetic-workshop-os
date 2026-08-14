from __future__ import annotations

import subprocess
from pathlib import Path

p = Path("scripts/check_documentation_lifecycle.py")
t = p.read_text(encoding="utf-8")
BASE = "a8a28672a6fd807cd59342a02a102b8e09128fff"
MANIFEST_SHA = subprocess.check_output(["git", "hash-object", "docs/history/d5-pre-decision/manifest.json"], text=True).strip()


def once(old: str, new: str) -> None:
    global t
    count = t.count(old)
    if count != 1:
        raise SystemExit(f"checker replacement mismatch {old!r}: {count}")
    t = t.replace(old, new, 1)


once(
    "D4-A, D4-B, D4-C and D4-D are lifecycle-closed. D4 is complete;\nD5, release readiness and Restore changes remain forbidden.",
    "D4-A, D4-B, D4-C and D4-D are lifecycle-closed. D4 is complete.\nCR-014 authorizes D5 only as documentation + exact-package assisted-install rehearsal;\nrelease/Phase-12/runtime expansion and Restore changes remain forbidden.",
)
once(
    'UPDATE_GUIDE = P("docs/update-guide.md")\n',
    'UPDATE_GUIDE = P("docs/update-guide.md")\nUSER_INSTALL = P("docs/user-install.md")\nREMOTE_INSTALL = P("docs/remote-install-checklist.md")\n',
)
once(
    'ADR20 = P("docs/decisions/0020-d4-update-safety-contract.md")\n',
    'ADR20 = P("docs/decisions/0020-d4-update-safety-contract.md")\nADR21 = P("docs/decisions/0021-d5-remote-install-rehearsal-contract.md")\n',
)
once(
    'D4D_PRECLOSURE_ABOUT = P("docs/history/d4-d-pre-closure/ABOUT.md")\n',
    'D4D_PRECLOSURE_ABOUT = P("docs/history/d4-d-pre-closure/ABOUT.md")\nD5_PREDECISION_MANIFEST = P("docs/history/d5-pre-decision/manifest.json")\nD5_PREDECISION_ABOUT = P("docs/history/d5-pre-decision/ABOUT.md")\n',
)
once(
    'D4D_PRECLOSURE_MANIFEST_SHA = "b403263c95c24aa02b884e97bc593d3d1aec9b58"\n',
    f'D4D_PRECLOSURE_MANIFEST_SHA = "b403263c95c24aa02b884e97bc593d3d1aec9b58"\nD5_DECISION_BASE = "{BASE}"\nD5_PREDECISION_MANIFEST_SHA = "{MANIFEST_SHA}"\n',
)

old_status = '''D4_STATUS = (
    "CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT",
    "D4 — Update safety — DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED",
    "D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED",
    "D4-D — Exact-package update verification and D4 lifecycle closure — DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED",
    "D5 — Remote install checklist — NOT AUTHORIZED BY CR-013",
    "Product release readiness — NOT CLAIMED",
)'''
new_status = '''D4_STATUS = (
    "CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT",
    "D4 — Update safety — DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED",
    "D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED",
    "D4-D — Exact-package update verification and D4 lifecycle closure — DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED",
)

D5_STATUS = (
    "CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT",
    "D5 — Remote install checklist — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "D5 verification — NOT STARTED",
    "PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014",
    "Product release readiness — NOT CLAIMED",
)'''
once(old_status, new_status)

# Replace the forbidden tuple wholesale to make the new D5 boundary explicit.
start = t.index("FORBIDDEN_ACTIVE = (\n")
end = t.index("\n)\n\nADR20_SECTIONS", start) + 2
t = t[:start] + '''FORBIDDEN_ACTIVE = (
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
)''' + t[end:]

# Snapshot verification for the exact pre-CR-014 active surfaces.
anchor = "\ndef check_legacy_protections() -> None:\n"
function = '''
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
        "docs-AGENTS.md", "current-focus.md", "progress.md", "handoff.md",
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

'''
if t.count(anchor) != 1:
    raise SystemExit("checker legacy anchor mismatch")
t = t.replace(anchor, function + anchor, 1)

# Current lifecycle now requires the D5 decision status everywhere.
once(
    "    for path in STATUS_SURFACES:\n        require(path, D4_STATUS)\n        forbid(path, FORBIDDEN_ACTIVE)",
    "    for path in STATUS_SURFACES:\n        require(path, D4_STATUS)\n        require(path, D5_STATUS)\n        forbid(path, FORBIDDEN_ACTIVE)",
)
once(
    'require(CURRENT, ("ADR 0020", "D4-A closure truth", "D4-B closure truth", "D4-C closure truth", "D4-D closure truth", "D4-D closure evidence", "D4 closure truth", D4D_VERIFIED_HEAD, D4D_FINAL_RUN, "Restore remains closed"))',
    'require(CURRENT, ("ADR 0020", "ADR 0021", "D4-A closure truth", "D4-B closure truth", "D4-C closure truth", "D4-D closure truth", "D4 closure truth", "D5 decision truth", D4D_VERIFIED_HEAD, D4D_FINAL_RUN, "Restore remains closed"))',
)
once(
    'require(PLAN, ("Normative D4 decision", "D4-A", "D4-B", "D4-C", "D4-D", "**DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED**"))',
    'require(PLAN, ("Normative D4 decision", "Normative D5 decision", "D4-A", "D4-B", "D4-C", "D4-D", "## D5 — Remote install checklist", "**AUTHORIZED NEXT — NOT IMPLEMENTED**"))',
)
once(
    'require(UPDATE_GUIDE, ("D4 Update Safety закрыт", "D5 всё ещё не авторизован", "старый пакет не является автоматическим откатом", "не включает автоматическое скачивание"))',
    'require(UPDATE_GUIDE, ("D4 Update Safety закрыт", "CR-014", "D5", "ещё не реализован/проверен", "старый пакет не является автоматическим откатом", "не включает автоматическое скачивание"))',
)
once(
    'require(DOCS_AGENTS, ("ADR 0020", "docs/domain-model-d4-update-safety.md"))',
    'require(DOCS_AGENTS, ("ADR 0020", "docs/domain-model-d4-update-safety.md", "ADR 0021", "documentation + exact-package assisted-install rehearsal"))',
)
once(
    'require(FOCUS, ("No further implementation slice is authorized by CR-013", "Starting D5 requires a separate authorization decision/change request"))',
    'require(FOCUS, ("Implement D5 Remote Install Checklist only", "documentation + exact-package assisted-install rehearsal", "Do not modify backend/frontend/launcher/migrations/package runtime"))\n    require(USER_INSTALL, ("DRAFT SKELETON — D5 AUTHORIZED BUT NOT IMPLEMENTED OR VERIFIED", "Terminal/Git/Python/Node/Docker"))\n    require(REMOTE_INSTALL, ("DRAFT SKELETON — D5 AUTHORIZED BUT NOT IMPLEMENTED OR VERIFIED", "ADR 0021"))',
)

# New ADR contract check.
insert_anchor = "\ndef check_domain_clarification() -> None:\n"
adr21_check = '''
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

'''
if t.count(insert_anchor) != 1:
    raise SystemExit("checker domain anchor mismatch")
t = t.replace(insert_anchor, adr21_check + insert_anchor, 1)

# Preserve old ADR20 truth: it may still say D5 was not authorized by CR-013; that is historical and scoped.
# Add snapshot/ADR21 checks to main.
once(
    "    check_d4d_preclosure_snapshot()\n    check_current_lifecycle()\n    check_adr20()",
    "    check_d4d_preclosure_snapshot()\n    check_d5_predecision_snapshot()\n    check_current_lifecycle()\n    check_adr20()\n    check_adr21()",
)
once(
    '    print("Verified D5 remains unauthorized and product release readiness remains not claimed.")',
    '    print("Verified CR-014 authorizes D5 only as documentation + exact-package assisted-install rehearsal.")\n    print("Verified D5 is not implemented/verified and Phase 12/product release readiness remain gated.")',
)

p.write_text(t, encoding="utf-8")
