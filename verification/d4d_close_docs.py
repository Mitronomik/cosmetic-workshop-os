from pathlib import Path
import os,re
HEAD=os.environ['D4D_VERIFIED_HEAD']; RUN=os.environ['D4D_RUN']; ART=os.environ['D4D_ARTIFACT']; DIG=os.environ['D4D_DIGEST']
OLD4='D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C DONE; D4-D AUTHORIZED NEXT'
NEW4='D4 — Update safety — DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED'
OLDD='D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED'
NEWD='D4-D — Exact-package update verification and D4 lifecycle closure — DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED'
SURF=('README.md','docs/current-lifecycle.md','docs/implementation-plan.md','docs/packaging.md','docs/deployment.md','state/current-focus.md','state/progress.md','state/handoff.md','state/change-requests.md')
for name in SURF:
 p=Path(name); t=p.read_text(encoding='utf-8')
 if OLD4 not in t or OLDD not in t: raise SystemExit(f'{name}: final D4 status source missing')
 p.write_text(t.replace(OLD4,NEW4).replace(OLDD,NEWD),encoding='utf-8')

def once(path,old,new):
 p=Path(path); t=p.read_text(encoding='utf-8')
 if t.count(old)!=1: raise SystemExit(f'{path}: narrative mismatch for {old!r}: {t.count(old)}')
 p.write_text(t.replace(old,new,1),encoding='utf-8')

once('README.md','D4-A, D4-B and D4-C are closed. D4-D is the only authorized next slice; D5 and release readiness remain gated.','D4-A, D4-B, D4-C and D4-D are closed. D4 is complete; D5 and product release readiness remain gated.')
p=Path('README.md'); t=p.read_text(encoding='utf-8')
pat=r'## D4-C closed baseline / D4-D next\n.*?(?=## Core product invariants)'
rep=f'''## D4 final closure

D4 Update Safety is **DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED**.

Final D4-D evidence:

- exact tested main/head: `{HEAD}`;
- final exact-package verifier run: `{RUN}`;
- evidence artifact: `{ART}`;
- artifact digest: `{DIG}`;
- final report: `PASS — FULL AUTOMATED SMOKE PASSED`;
- one exact current-main `.app` was reused across the D4-C human-status/failure matrix and the accepted D4-B staging/interruption/newer-lineage matrix;
- isolated user-data remained outside the repository/package and the repository postflight was clean.

D5 is not authorized by CR-013 and product release readiness is not claimed.

'''
t2,n=re.subn(pat,rep,t,count=1,flags=re.S)
if n!=1: raise SystemExit('README final D4 section mismatch')
p.write_text(t2,encoding='utf-8')

once('docs/current-lifecycle.md','D4-A, D4-B and D4-C are closed. D4-D is the only authorized next slice.','D4-A, D4-B, D4-C and D4-D are closed. D4 is lifecycle-closed.')
p=Path('docs/current-lifecycle.md'); t=p.read_text(encoding='utf-8')
pat=r'## D4-D authorization boundary\n.*?(?=## Closed Restore boundary)'
rep=f'''## D4-D closure truth

D4-D is **DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED**. It introduced no runtime implementation. It re-verified the complete D4 manual-update safety contract on exact current main `{HEAD}` using one real packaged `.app`, the full regression/lifecycle/frontend/package path, the D4-C human status/failure scenarios, and the accepted D4-B staged-migration/interruption/newer-lineage matrix.

## D4-D closure evidence

- exact tested main/head: `{HEAD}`;
- final D4-D verifier run: `{RUN}`;
- evidence artifact: `{ART}`;
- artifact digest: `{DIG}`;
- final result: `PASS — FULL AUTOMATED SMOKE PASSED`.

## D4 closure truth

D4 Update Safety is **DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED**. CR-013 authorizes no further implementation slice. D5 remains **NOT AUTHORIZED BY CR-013**, and product release readiness remains **NOT CLAIMED**. A future D5 start requires a separate authorization decision/change request.

'''
t2,n=re.subn(pat,rep,t,count=1,flags=re.S)
if n!=1: raise SystemExit('current lifecycle D4-D section mismatch')
p.write_text(t2,encoding='utf-8')

once('docs/implementation-plan.md','D4-A, D4-B and D4-C are closed. D4-D is the only authorized next slice.','D4-A, D4-B, D4-C and D4-D are closed. D4 is complete.')
p=Path('docs/implementation-plan.md'); t=p.read_text(encoding='utf-8')
old='''**AUTHORIZED NEXT — NOT IMPLEMENTED**.\n\nD4-D is limited to final exact-package verification of the complete ADR 0020 D4 manual-update safety contract and D4 lifecycle closure. It must not introduce new update runtime authority, downloader/checking, D5, release/distribution work or Restore changes.'''
new=f'''**DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED**.\n\nExact current main `{HEAD}` passed final D4-D run `{RUN}` with the complete D4 package safety matrix. D4 is lifecycle-closed. No D5 or release work is authorized by this closure.'''
if t.count(old)!=1: raise SystemExit('implementation-plan D4-D narrative mismatch')
p.write_text(t.replace(old,new,1),encoding='utf-8')

once('docs/packaging.md','Status: **CURRENT — D3 IMPLEMENTED; D4-A/B/C CLOSED; D4-D AUTHORIZED NEXT**','Status: **CURRENT — D3 IMPLEMENTED; D4 CLOSED AND FINAL EXACT-PACKAGE VERIFIED**')
once('docs/packaging.md','D4-C closure authorizes D4-D only. It does not authorize auto-update download, internet update checking, GitHub Releases integration, release channels, installer redesign, signing/notarization, DMG, App Store, sandbox migration, D5 or release readiness.','D4 is closed and final exact-package verified. This closure does not authorize auto-update download, internet update checking, GitHub Releases integration, release channels, installer redesign, signing/notarization, DMG, App Store, sandbox migration, D5 or release readiness.')
once('docs/deployment.md','Closed D4-C adds no deployment topology: Settings uses the existing local API and packaged failures use the existing package entrypoint. D4-D alone is authorized next; D5 and release/distribution/cloud work remain unauthorized.','D4 is closed with no deployment-topology change: Settings uses the existing local API and packaged failures use the existing package entrypoint. D5 and release/distribution/cloud work remain unauthorized.')
once('docs/update-guide.md','Статус: **D4-A, D4-B и D4-C закрыты и проверены; D4-D авторизован следующим только для финальной exact-package проверки D4 и lifecycle closure**.','Статус: **D4 Update Safety закрыт и финально exact-package проверен**.')
once('docs/update-guide.md','Этот файл пока **не является инструкцией о готовом обновлении продукта**. D4-A, D4-B и D4-C закрыты и exact-package проверены. D4-D теперь авторизован только для финальной проверки полного D4-контракта и lifecycle closure; готовность продукта к релизу всё ещё не заявлена.','D4-контракт безопасного ручного обновления реализован и финально exact-package проверен. Этот файл описывает update-safety поведение, но не является заявлением о готовности продукта к релизу или о завершённой удалённой установке: D5 всё ещё не авторизован.')

Path('state/current-focus.md').write_text(f'''# Current focus\n\nUpdated: `2026-08-14`\n\n## Current lifecycle\n\n```text\nC4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED\nRestore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED\nD3 — macOS package MVP — IMPLEMENTED\nCR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT\n{NEW4}\nD4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED\nD4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED\nD4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED\n{NEWD}\nD5 — Remote install checklist — NOT AUTHORIZED BY CR-013\nProduct release readiness — NOT CLAIMED\n```\n\n## Current task\n\n**No further implementation slice is authorized by CR-013.**\n\nD4 is complete and lifecycle-closed. Starting D5 requires a separate authorization decision/change request. Until then, do not implement remote-install work, auto-update/download, signing/notarization/DMG/App Store/release channels, product release readiness claims or Restore changes.\n\n## Final D4 evidence\n\n- exact tested main/head: `{HEAD}`;\n- D4-D run: `{RUN}`; artifact `{ART}`; digest `{DIG}`;\n- final result: `PASS — FULL AUTOMATED SMOKE PASSED`.\n''',encoding='utf-8')

once('state/progress.md','D4-B remains closed. D4-C is now merged, exact-head/exact-package verified and lifecycle-closed. Verified PR head `ba577f1151e041c11019525862d9bb76eeb1404e` and merged head `3d69df192b5bdff9c7df067d8c8fde40154ebac9` are content-identical; Level-5 runs `31747841343` and `31749503618` both passed.\n\nD4-D alone is authorized next. D5 and release readiness remain gated.',f'D4-A/B/C remain closed. D4-D final exact-package verification passed on `{HEAD}` in run `{RUN}`; D4 is now lifecycle-closed.\n\nD5 remains unauthorized by CR-013 and product release readiness remains not claimed.')
once('state/handoff.md','- D4-D is AUTHORIZED NEXT — not implemented.','- D4-D is DONE — final exact-package verification passed; D4 is lifecycle-closed.')
once('state/handoff.md','## D4-C closed handoff / D4-D next','## D4 final closed handoff')
once('state/handoff.md','D4-C is closed on verified PR head `ba577f1151e041c11019525862d9bb76eeb1404e` and merged head `3d69df192b5bdff9c7df067d8c8fde40154ebac9` with Level-5 runs `31747841343` / `31749503618` and a `0`-file head→merge compare. D4-D may now perform only final exact-package D4 verification and lifecycle closure; do not widen into D5, release work or Restore.',f'D4-C remains closed. D4-D final verification passed on exact main `{HEAD}` in run `{RUN}` and D4 is lifecycle-closed. No D5, release or Restore work is authorized by this closure.')
once('state/change-requests.md','Status: **ACCEPTED — D4-A/B/C CLOSED; D4-D AUTHORIZED NEXT**.','Status: **ACCEPTED — D4 CLOSED; NO D5 AUTHORIZATION**.')
once('state/change-requests.md','D4-A, D4-B and D4-C are closed. D4-C verified PR head `ba577f1151e041c11019525862d9bb76eeb1404e` and merged head `3d69df192b5bdff9c7df067d8c8fde40154ebac9` passed Level-5 exact-package verification and are content-identical. D4-D alone is authorized next.',f'D4-A/B/C remain closed. D4-D final exact-package verification passed on exact main `{HEAD}` in run `{RUN}`. D4 is lifecycle-closed; CR-013 provides no D5 authorization.')
once('state/change-requests.md','D4-A/B/C closure remains satisfied. D4-D only is authorized next; D5 and release readiness remain unauthorized/not claimed.','D4-A/B/C/D closure is satisfied. D5 remains unauthorized and product release readiness remains not claimed.')

idx=Path('docs/history/README.md'); t=idx.read_text(encoding='utf-8'); anchor='## Current index\n\n'; entry=f'- `d4-d-pre-closure/` — exact active lifecycle/state/checker surfaces from `{HEAD}` immediately before final D4-D/D4 lifecycle closure.\n'
if t.count(anchor)!=1: raise SystemExit('history index anchor mismatch')
idx.write_text(t.replace(anchor,anchor+entry,1),encoding='utf-8')
