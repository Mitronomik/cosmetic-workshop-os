from pathlib import Path
p=Path('docs/implementation-plan.md')
t=p.read_text(encoding='utf-8')
items=[
('D4-A remains merged, exact-head verified and lifecycle-closed. D4-B is also merged, verified and closed; D4-C is now the only authorized next slice.','D4-A and D4-B remain closed. D4-C is implemented in the current branch and awaits exact-head/exact-package verification and lifecycle closure.'),
('D4-B closure conditions are satisfied on merged head `d60a3be993c76b59292cf27ee66bcbe856669fc4`. D4-C is authorized next as a separate bounded PR.','D4-B closure remains satisfied. D4-C is implemented separately and remains verification-pending.'),
('**AUTHORIZED NEXT — NOT IMPLEMENTED**.','''**IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING**.

Implementation code commit: `adfe37a3f68a545635f173c22d4710eacde86e74`.

Implemented scope: redacted backend-owned Settings update status; compact read-only Settings presentation; two fixed packaged update-failure outcomes; no update controls or raw metadata; no protected Restore changes; focused backend/package/frontend tests.

D4-D remains unauthorized until D4-C is merged, verified and lifecycle-closed.'''),
]
for old,new in items:
    if t.count(old)!=1: raise SystemExit('implementation-plan transition mismatch')
    t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')
