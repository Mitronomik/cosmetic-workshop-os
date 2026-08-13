from __future__ import annotations

import os
from pathlib import Path
import subprocess

MERGED_HEAD = os.environ["D4C_MERGED_HEAD"]
PR_HEAD = os.environ["D4C_VERIFIED_PR_HEAD"]
PR_RUN = os.environ["D4C_PR_HEAD_RUN"]
MERGED_RUN = os.environ["D4C_MERGED_RUN"]
MANIFEST_SHA = subprocess.check_output(["git", "hash-object", "docs/history/d4-c-pre-closure/manifest.json"], text=True).strip()

p = Path("scripts/check_documentation_lifecycle.py")
t = p.read_text(encoding="utf-8")


def once(old: str, new: str) -> None:
    global t
    if t.count(old) != 1:
        raise SystemExit(f"checker replacement mismatch for {old!r}: {t.count(old)}")
    t = t.replace(old, new, 1)


once(
    "D4-A and D4-B are closed. D4-C is implemented but verification/lifecycle closure\nremain pending; D4-D/D5, release readiness and Restore changes remain forbidden.",
    "D4-A, D4-B and D4-C are lifecycle-closed. D4-D alone is authorized next;\nD5, release readiness and Restore changes remain forbidden.",
)
once(
    'D4B_PRECLOSURE_ABOUT = P("docs/history/d4-b-pre-closure/ABOUT.md")\n',
    'D4B_PRECLOSURE_ABOUT = P("docs/history/d4-b-pre-closure/ABOUT.md")\nD4C_PRECLOSURE_MANIFEST = P("docs/history/d4-c-pre-closure/manifest.json")\nD4C_PRECLOSURE_ABOUT = P("docs/history/d4-c-pre-closure/ABOUT.md")\n',
)
once(
    'D4C_IMPLEMENTATION_CODE_COMMIT = "adfe37a3f68a545635f173c22d4710eacde86e74"\n',
    f'D4C_IMPLEMENTATION_CODE_COMMIT = "adfe37a3f68a545635f173c22d4710eacde86e74"\nD4C_VERIFIED_PR_HEAD = "{PR_HEAD}"\nD4C_MERGED_HEAD = "{MERGED_HEAD}"\nD4C_PR_HEAD_RUN = "{PR_RUN}"\nD4C_MERGED_RUN = "{MERGED_RUN}"\nD4C_PRECLOSURE_MANIFEST_SHA = "{MANIFEST_SHA}"\n',
)

start = t.index("D4_STATUS = (\n")
end = t.index("\n)\n\nCLOSED_TRUTH", start) + 2
t = t[:start] + '''D4_STATUS = (
    "CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT",
    "D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C DONE; D4-D AUTHORIZED NEXT",
    "D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED",
    "D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "D5 — Remote install checklist — NOT AUTHORIZED BY CR-013",
    "Product release readiness — NOT CLAIMED",
)''' + t[end:]

start = t.index("FORBIDDEN_ACTIVE = (\n")
end = t.index("\n)\n\nADR20_SECTIONS", start) + 2
t = t[:start] + '''FORBIDDEN_ACTIVE = (
    "D4 — Update safety — IN PROGRESS — D4-C IMPLEMENTED, VERIFICATION PENDING",
    "D4-C — User-facing update status and packaged failure UX — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING",
    "D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C AUTHORIZED NEXT",
    "D4-C — User-facing update status and packaged failure UX — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED",
    "D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED",
    "D4 — Update safety — DONE",
    "D4 — Update safety — CLOSED",
    "D4-D — Exact-package update verification and D4 lifecycle closure — IMPLEMENTED",
    "D4-D — Exact-package update verification and D4 lifecycle closure — DONE",
    "D4-D — Exact-package update verification and D4 lifecycle closure — CLOSED",
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
)''' + t[end:]

anchor = "\ndef check_legacy_protections() -> None:\n"
function = f'''
def check_d4c_preclosure_snapshot() -> None:
    verify_blob(D4C_PRECLOSURE_MANIFEST, D4C_PRECLOSURE_MANIFEST_SHA, "D4-C pre-closure manifest")
    try:
        payload = json.loads(read(D4C_PRECLOSURE_MANIFEST))
    except json.JSONDecodeError as exc:
        ERRORS.append(f"D4-C pre-closure manifest does not parse: {{exc}}")
        return
    if payload.get("source_commit") != D4C_MERGED_HEAD: ERRORS.append("D4-C pre-closure manifest source commit changed")
    if payload.get("verified_pr_head") != D4C_VERIFIED_PR_HEAD: ERRORS.append("D4-C pre-closure verified PR head changed")
    if payload.get("pr_head_verification_run") != D4C_PR_HEAD_RUN: ERRORS.append("D4-C pre-closure PR-head verification run changed")
    if payload.get("merged_head_verification_run") != D4C_MERGED_RUN: ERRORS.append("D4-C pre-closure merged-head verification run changed")
    if payload.get("verified_head_to_merge_changed_files") != 0: ERRORS.append("D4-C verified-head to merge file count changed")
    files = payload.get("files", {{}})
    expected_names = ('README.md','current-lifecycle.md','implementation-plan.md','packaging.md','deployment.md','update-guide.md','current-focus.md','progress.md','handoff.md','change-requests.md','check_documentation_lifecycle.py','history-README.md')
    if set(files) != set(expected_names): ERRORS.append(f"D4-C pre-closure manifest file set changed: {{sorted(files)}}")
    for name in expected_names:
        expected = files.get(name)
        if isinstance(expected, str): verify_blob(P(f"docs/history/d4-c-pre-closure/{{name}}"), expected, "D4-C pre-closure snapshot blob")
    require(D4C_PRECLOSURE_ABOUT, (D4C_MERGED_HEAD, D4C_VERIFIED_PR_HEAD, D4C_PR_HEAD_RUN, D4C_MERGED_RUN, "`0` changed files", "exact Git blob identity"))
    require(HISTORY_INDEX, ("d4-c-pre-closure/", D4C_MERGED_HEAD))

'''
if t.count(anchor) != 1: raise SystemExit("checker legacy anchor mismatch")
t = t.replace(anchor, function + anchor, 1)

once(
    'require(CURRENT, ("ADR 0020", "D4-A closure truth", "D4-A closure evidence", "D4-B closure truth", "D4-B closure evidence", "D4-C implementation truth", "D4-C verification boundary", D4C_IMPLEMENTATION_CODE_COMMIT, "Restore remains closed"))',
    'require(CURRENT, ("ADR 0020", "D4-A closure truth", "D4-A closure evidence", "D4-B closure truth", "D4-B closure evidence", "D4-C closure truth", "D4-C closure evidence", "D4-D authorization boundary", D4C_VERIFIED_PR_HEAD, D4C_MERGED_HEAD, "Restore remains closed"))',
)
once(
    'require(UPDATE_GUIDE, ("D4-A и D4-B закрыты", "D4-C реализован", "старый пакет не является автоматическим откатом", "не включает автоматическое скачивание"))',
    'require(UPDATE_GUIDE, ("D4-A, D4-B и D4-C закрыты", "D4-D", "старый пакет не является автоматическим откатом", "не включает автоматическое скачивание"))',
)
once(
    "    check_d4b_preclosure_snapshot()\n    check_current_lifecycle()",
    "    check_d4b_preclosure_snapshot()\n    check_d4c_preclosure_snapshot()\n    check_current_lifecycle()",
)
once(
    '    print("Verified D4-C is implemented but exact-head/exact-package verification and lifecycle closure remain pending.")\n    print("Verified D4-D, D5 and product release readiness remain gated.")',
    '    print("Verified D4-C is lifecycle-closed on exact PR-head and merged-head Level-5 evidence.")\n    print("Verified D4-D alone is authorized next; D5 and product release readiness remain gated.")',
)

p.write_text(t, encoding="utf-8")
