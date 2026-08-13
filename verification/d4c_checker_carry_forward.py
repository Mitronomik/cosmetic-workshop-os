from pathlib import Path
p=Path('scripts/check_documentation_lifecycle.py')
t=p.read_text(encoding='utf-8')
anchor='    "D4-C — User-facing update status and packaged failure UX — AUTHORIZED NEXT — NOT IMPLEMENTED",\n'
extra='''    "D4 — Update safety — IN PROGRESS — D4-B IMPLEMENTED, VERIFICATION PENDING",
    "D4-B — Safe migration execution and durable UpdateLog — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING",
    "D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED",
    "D4 — Update safety — IN PROGRESS — D4-A IMPLEMENTED, VERIFICATION PENDING",
    "D4-A — Version identity and compatibility preflight — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING",
    "D4-B — Safe migration execution and durable UpdateLog — PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED",
'''
if t.count(anchor)!=1: raise SystemExit('forbidden carry-forward anchor mismatch')
t=t.replace(anchor,anchor+extra,1)
for old,new in [
('    "Product release readiness — CLAIMED",\n','    "Product release readiness — CLAIMED",\n    "Product release readiness — ACHIEVED",\n'),
('require(UPDATE_GUIDE, ("D4-A закрыт", "D4-B закрыт", "старый пакет не является автоматическим откатом", "не включает автоматическое скачивание"))','require(UPDATE_GUIDE, ("D4-A и D4-B закрыты", "D4-C реализован", "старый пакет не является автоматическим откатом", "не включает автоматическое скачивание"))'),
('require(D4C_BINDINGS, ("mountSettingsUpdateStatus", "data-tax-rate-section"))','require(D4C_BINDINGS, ("mountSettingsUpdateStatus",))'),
]:
 if t.count(old)!=1: raise SystemExit('checker carry-forward replacement mismatch')
 t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')
