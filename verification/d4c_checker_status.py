from pathlib import Path
p=Path('scripts/check_documentation_lifecycle.py')
t=p.read_text(encoding='utf-8')
t=t.replace('D4-A and D4-B are closed. D4-C alone may implement bounded user-facing update\nstatus/failure UX; it may not authorize D4-D/D5, claim release readiness or reopen Restore.','D4-A and D4-B are closed. D4-C is implemented but verification/lifecycle closure\nremain pending; D4-D/D5, release readiness and Restore changes remain forbidden.',1)
anchor='D4B_TEST = P("backend/app/tests/test_d4_b_update_safety.py")\n'
add='''D4C_SETTINGS_SCHEMA = P("backend/app/schemas/settings.py")
D4C_SETTINGS_SERVICE = P("backend/app/services/settings.py")
D4C_FRONTEND = P("frontend/src/settings-update-status.ts")
D4C_BINDINGS = P("frontend/src/settings-tax-bindings.ts")
D4C_PACKAGE_ENTRYPOINT = P("macos_package/entrypoint.py")
D4C_USER_ALERT = P("macos_package/user_alert.py")
D4C_BACKEND_TEST = P("backend/app/tests/test_d4_c_update_status.py")
D4C_FRONTEND_TEST = P("frontend/test/settings-update-status.test.mjs")
D4C_PACKAGE_TEST = P("macos_package/tests/test_d4_c_update_failure_alerts.py")
'''
if t.count(anchor)!=1: raise SystemExit('D4C constants anchor mismatch')
t=t.replace(anchor,anchor+add,1)
sha='D4B_PRECLOSURE_MANIFEST_SHA = "e3c1bd273e3eb2f248c8497fd36bf920be3def99"\n'
if t.count(sha)!=1: raise SystemExit('D4C sha anchor mismatch')
t=t.replace(sha,sha+'D4C_IMPLEMENTATION_CODE_COMMIT = "adfe37a3f68a545635f173c22d4710eacde86e74"\n',1)
old='''D4_STATUS = (
    "CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT",
    "D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C AUTHORIZED NEXT",
    "D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED",
    "D4-C — User-facing update status and packaged failure UX — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED",
    "D5 — Remote install checklist — NOT AUTHORIZED BY CR-013",
    "Product release readiness — NOT CLAIMED",
)'''
new=old.replace('D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C AUTHORIZED NEXT','D4 — Update safety — IN PROGRESS — D4-C IMPLEMENTED, VERIFICATION PENDING').replace('D4-C — User-facing update status and packaged failure UX — AUTHORIZED NEXT — NOT IMPLEMENTED','D4-C — User-facing update status and packaged failure UX — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING')
if t.count(old)!=1: raise SystemExit('D4_STATUS mismatch')
t=t.replace(old,new,1)
start=t.index('FORBIDDEN_ACTIVE = (\n'); end=t.index('\n)\n\nADR20_SECTIONS',start)+2
forbidden='''FORBIDDEN_ACTIVE = (
    "D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C AUTHORIZED NEXT",
    "D4-C — User-facing update status and packaged failure UX — AUTHORIZED NEXT — NOT IMPLEMENTED",
    "D4-C — User-facing update status and packaged failure UX — DONE",
    "D4-C — User-facing update status and packaged failure UX — CLOSED",
    "D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT",
    "D4-D — Exact-package update verification and D4 lifecycle closure — IMPLEMENTED",
    "D5 — Remote install checklist — AUTHORIZED",
    "D5 — Remote install checklist — IMPLEMENTED",
    "Product release readiness — READY",
    "Product release readiness — CLAIMED",
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
t=t[:start]+forbidden+t[end:]
t=t.replace('require(CURRENT, ("ADR 0020", "D4-A closure truth", "D4-A closure evidence", "D4-B closure truth", "D4-B closure evidence", "D4-C authorization boundary", "Restore remains closed"))','require(CURRENT, ("ADR 0020", "D4-A closure truth", "D4-A closure evidence", "D4-B closure truth", "D4-B closure evidence", "D4-C implementation truth", "D4-C verification boundary", D4C_IMPLEMENTATION_CODE_COMMIT, "Restore remains closed"))',1)
p.write_text(t,encoding='utf-8')
