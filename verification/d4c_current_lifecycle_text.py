from pathlib import Path
p=Path('docs/current-lifecycle.md')
t=p.read_text(encoding='utf-8')
items=[
('D4-A remains merged and exact-head verified. D4-B is now merged, exact-head/exact-package verified and lifecycle-closed; D4-C alone is authorized next.','D4-A and D4-B remain closed. D4-C is implemented in the current branch; exact-head/exact-package verification and lifecycle closure remain pending, and D4-D remains unauthorized.'),
('D4-B is **DONE — MERGED AND VERIFIED**. Exact PR-head Level-5 run `31716610699` and exact merged-head Level-5 run `31717705331` both passed; implementation head `8688fa3dba87205b4b4626ebab2902262fd4cd24` and merge commit `d60a3be993c76b59292cf27ee66bcbe856669fc4` are content-identical. D4-C is the only authorized next slice.','D4-B is **DONE — MERGED AND VERIFIED**. Its accepted Level-5 evidence remains authoritative; D4-C adds presentation only and does not change D4-B migration semantics.'),
('Restore remains closed. D4-A changes no protected Restore production blob, no Restore state machine, picker, source proof, control plane, backend handshake, replacement or recovery semantics.','Restore remains closed. D4-C changes no protected Restore production blob, no Restore state machine, picker, source proof, control plane, backend handshake, replacement or recovery semantics.'),
]
for old,new in items:
    if t.count(old)!=1: raise SystemExit('current lifecycle text mismatch')
    t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')
