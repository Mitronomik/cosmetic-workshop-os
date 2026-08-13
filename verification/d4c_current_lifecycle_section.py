from pathlib import Path
p=Path('docs/current-lifecycle.md')
t=p.read_text(encoding='utf-8')
old='## D4-C authorization boundary\n\nThis closure authorizes **D4-C only**: bounded user-facing update status and packaged failure UX. It does not authorize D4-D, D5, auto-download/update checking, signing, notarization, DMG, App Store, release channels, release readiness or Restore changes.'
new='''## D4-C implementation truth

Implementation code commit: `adfe37a3f68a545635f173c22d4710eacde86e74`.

D4-C projects D4-B startup truth into a bounded read-only Settings status and two fixed packaged failure outcomes. It exposes no raw update metadata, paths or tracebacks and creates no browser update command. The before-commit outcome claims only that canonical DB replacement did not occur; the uncertain outcome makes no rollback/data-unchanged claim. Closed Restore production blobs remain unchanged.

D4-C is **IMPLEMENTED — VERIFICATION PENDING**, not lifecycle-closed.

## D4-C verification boundary

The exact published PR head still requires full regression, lifecycle integrity, frontend build, real macOS package and exact-package D4-C smoke. D4-D, D5, release/distribution work and Restore changes remain unauthorized.'''
if t.count(old)!=1: raise SystemExit('D4-C lifecycle section mismatch')
p.write_text(t.replace(old,new,1),encoding='utf-8')
