from pathlib import Path
import os,subprocess
p=Path('scripts/check_documentation_lifecycle.py'); t=p.read_text(encoding='utf-8')
HEAD=os.environ['D4D_VERIFIED_HEAD']; RUN=os.environ['D4D_RUN']; manifest_sha=subprocess.check_output(['git','hash-object','docs/history/d4-d-pre-closure/manifest.json'],text=True).strip()
def once(old,new):
 global t
 if t.count(old)!=1: raise SystemExit(f'checker replacement mismatch {old!r}: {t.count(old)}')
 t=t.replace(old,new,1)
once('D4-A, D4-B and D4-C are lifecycle-closed. D4-D alone is authorized next;\nD5, release readiness and Restore changes remain forbidden.','D4-A, D4-B, D4-C and D4-D are lifecycle-closed. D4 is complete;\nD5, release readiness and Restore changes remain forbidden.')
once('D4C_PRECLOSURE_ABOUT = P("docs/history/d4-c-pre-closure/ABOUT.md")\n','D4C_PRECLOSURE_ABOUT = P("docs/history/d4-c-pre-closure/ABOUT.md")\nD4D_PRECLOSURE_MANIFEST = P("docs/history/d4-d-pre-closure/manifest.json")\nD4D_PRECLOSURE_ABOUT = P("docs/history/d4-d-pre-closure/ABOUT.md")\n')
once('D4C_PRECLOSURE_MANIFEST_SHA = "22271c8327e3af235c52de88f6654a1f3808e54f"\n',f'D4C_PRECLOSURE_MANIFEST_SHA = "22271c8327e3af235c52de88f6654a1f3808e54f"\nD4D_VERIFIED_HEAD = "{HEAD}"\nD4D_FINAL_RUN = "{RUN}"\nD4D_PRECLOSURE_MANIFEST_SHA = "{manifest_sha}"\n')
start=t.index('D4_STATUS = (\n'); end=t.index('\n)\n\nCLOSED_TRUTH',start)+2
t=t[:start]+'''D4_STATUS = (
    "CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT",
    "D4 — Update safety — DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED",
    "D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED",
    "D4-D — Exact-package update verification and D4 lifecycle closure — DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED",
    "D5 — Remote install checklist — NOT AUTHORIZED BY CR-013",
    "Product release readiness — NOT CLAIMED",
)'''+t[end:]
start=t.index('FORBIDDEN_ACTIVE = (\n'); end=t.index('\n)\n\nADR20_SECTIONS',start)+2
block='''FORBIDDEN_ACTIVE = (
    "D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C DONE; D4-D AUTHORIZED NEXT",
    "D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "D4 — Update safety — IN PROGRESS — D4-C IMPLEMENTED, VERIFICATION PENDING",
    "D4 — Update safety — IN PROGRESS — D4-B IMPLEMENTED, VERIFICATION PENDING",
    "D4 — Update safety — IN PROGRESS — D4-A IMPLEMENTED, VERIFICATION PENDING",
    "D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED",
    "D4-D — Exact-package update verification and D4 lifecycle closure — IMPLEMENTED",
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
)'''
t=t[:start]+block+t[end:]
anchor='\ndef check_legacy_protections() -> None:\n'
fn=f'''
def check_d4d_preclosure_snapshot() -> None:
    verify_blob(D4D_PRECLOSURE_MANIFEST, D4D_PRECLOSURE_MANIFEST_SHA, "D4-D pre-closure manifest")
    try: payload=json.loads(read(D4D_PRECLOSURE_MANIFEST))
    except json.JSONDecodeError as exc:
        ERRORS.append(f"D4-D pre-closure manifest does not parse: {{exc}}")
        return
    if payload.get("source_commit") != D4D_VERIFIED_HEAD: ERRORS.append("D4-D pre-closure source commit changed")
    if payload.get("d4d_final_verification_run") != D4D_FINAL_RUN: ERRORS.append("D4-D final verification run changed")
    files=payload.get("files", {{}})
    expected_names=('README.md','current-lifecycle.md','implementation-plan.md','packaging.md','deployment.md','update-guide.md','current-focus.md','progress.md','handoff.md','change-requests.md','check_documentation_lifecycle.py','history-README.md')
    if set(files) != set(expected_names): ERRORS.append(f"D4-D pre-closure manifest file set changed: {{sorted(files)}}")
    for name in expected_names:
        expected=files.get(name)
        if isinstance(expected,str): verify_blob(P(f"docs/history/d4-d-pre-closure/{{name}}"),expected,"D4-D pre-closure snapshot blob")
    require(D4D_PRECLOSURE_ABOUT,(D4D_VERIFIED_HEAD,D4D_FINAL_RUN,"PASS — FULL AUTOMATED SMOKE PASSED","exact Git blob identity"))
    require(HISTORY_INDEX,("d4-d-pre-closure/",D4D_VERIFIED_HEAD))

'''
if t.count(anchor)!=1: raise SystemExit('checker function anchor mismatch')
t=t.replace(anchor,fn+anchor,1)
once('require(CURRENT, ("ADR 0020", "D4-A closure truth", "D4-A closure evidence", "D4-B closure truth", "D4-B closure evidence", "D4-C closure truth", "D4-C closure evidence", "D4-D authorization boundary", D4C_VERIFIED_PR_HEAD, D4C_MERGED_HEAD, "Restore remains closed"))','require(CURRENT, ("ADR 0020", "D4-A closure truth", "D4-B closure truth", "D4-C closure truth", "D4-D closure truth", "D4-D closure evidence", "D4 closure truth", D4D_VERIFIED_HEAD, D4D_FINAL_RUN, "Restore remains closed"))')
once('require(PLAN, ("Normative D4 decision", "D4-A", "D4-B", "D4-C", "D4-D", "**AUTHORIZED NEXT — NOT IMPLEMENTED**"))','require(PLAN, ("Normative D4 decision", "D4-A", "D4-B", "D4-C", "D4-D", "**DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED**"))')
once('require(UPDATE_GUIDE, ("D4-A, D4-B и D4-C закрыты", "D4-D", "старый пакет не является автоматическим откатом", "не включает автоматическое скачивание"))','require(UPDATE_GUIDE, ("D4 Update Safety закрыт", "D5 всё ещё не авторизован", "старый пакет не является автоматическим откатом", "не включает автоматическое скачивание"))')
once('    check_d4c_preclosure_snapshot()\n    check_current_lifecycle()','    check_d4c_preclosure_snapshot()\n    check_d4d_preclosure_snapshot()\n    check_current_lifecycle()')
once('    print("Verified D4-C is lifecycle-closed on exact PR-head and merged-head Level-5 evidence.")\n    print("Verified D4-D alone is authorized next; D5 and product release readiness remain gated.")','    print("Verified D4 is lifecycle-closed on final D4-D exact-package evidence.")\n    print("Verified D5 remains unauthorized and product release readiness remains not claimed.")')
# Explicitly protect the no-next-slice boundary.
once('    require(DOCS_AGENTS, ("ADR 0020", "docs/domain-model-d4-update-safety.md"))','    require(DOCS_AGENTS, ("ADR 0020", "docs/domain-model-d4-update-safety.md"))\n    require(FOCUS, ("No further implementation slice is authorized by CR-013", "Starting D5 requires a separate authorization decision/change request"))')
p.write_text(t,encoding='utf-8')
