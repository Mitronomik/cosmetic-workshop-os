from pathlib import Path

def once(path,old,new):
    p=Path(path); t=p.read_text(encoding='utf-8')
    if t.count(old)!=1: raise SystemExit(f'{path}: narrative source mismatch {old!r}: {t.count(old)}')
    p.write_text(t.replace(old,new,1),encoding='utf-8')

once('docs/current-lifecycle.md','D5, auto-update/download, GitHub Releases integration, signing, notarization, DMG, App Store, release channels and release readiness remain outside CR-013/D4-A.','D4 is closed. D5, auto-update/download, GitHub Releases integration, signing, notarization, DMG, App Store, release channels and release readiness remain unauthorized or not claimed and require separate future authorization.')
once('README.md','Read `AGENTS.md`, `docs/current-lifecycle.md`, relevant ADRs and the focused product/domain/test docs before changing behavior. Current D4 work must follow ADR 0020 and must not reopen the closed Restore boundary.','Read `AGENTS.md`, `docs/current-lifecycle.md`, relevant ADRs and the focused product/domain/test docs before changing behavior. D4 is closed; any future update/distribution work requires a new authorized lifecycle step and must not reopen the closed Restore boundary.')
once('docs/update-guide.md','Принятый будущий пользовательский сценарий:','Принятый пользовательский сценарий безопасной ручной замены:')
once('state/progress.md','## D4-B closure','## D4 closure')

checker=Path('scripts/check_documentation_lifecycle.py'); t=checker.read_text(encoding='utf-8')
anchor='    "D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED",\n'
extra='''    "D4-D alone is authorized next",
    "D4-D is the only authorized next slice",
    "D4-D may now perform only final exact-package D4 verification",
    "D4-D авторизован следующим",
    "remain outside CR-013/D4-A",
'''
if t.count(anchor)!=1: raise SystemExit('checker D4 final narrative anchor mismatch')
t=t.replace(anchor,anchor+extra,1)
checker.write_text(t,encoding='utf-8')
