from pathlib import Path

plan = Path('docs/implementation-plan.md')
text = plan.read_text(encoding='utf-8')
old = '**PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED**.'
new = '''**AUTHORIZED NEXT — NOT IMPLEMENTED**.

D4-D is limited to final exact-package verification of the complete ADR 0020 D4 manual-update safety contract and D4 lifecycle closure. It must not introduce new update runtime authority, downloader/checking, D5, release/distribution work or Restore changes.'''
if text.count(old) != 1:
    raise SystemExit(f'implementation-plan stale D4-D marker mismatch: {text.count(old)}')
plan.write_text(text.replace(old, new, 1), encoding='utf-8')

checker = Path('scripts/check_documentation_lifecycle.py')
text = checker.read_text(encoding='utf-8')
anchor = '    "D4 — Update safety — IN PROGRESS — D4-C IMPLEMENTED, VERIFICATION PENDING",\n'
extra = '''    "D4-A and D4-B remain closed. D4-C is implemented in the current branch; exact-head/exact-package verification and lifecycle closure remain pending, and D4-D remains unauthorized.",
    "**PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED**.",
'''
if text.count(anchor) != 1:
    raise SystemExit('checker stale-narrative anchor mismatch')
text = text.replace(anchor, anchor + extra, 1)
old_require = 'require(PLAN, ("Normative D4 decision", "D4-A", "D4-B", "D4-C", "D4-D"))'
new_require = 'require(PLAN, ("Normative D4 decision", "D4-A", "D4-B", "D4-C", "D4-D", "**AUTHORIZED NEXT — NOT IMPLEMENTED**"))'
if text.count(old_require) != 1:
    raise SystemExit('checker plan requirement anchor mismatch')
checker.write_text(text.replace(old_require, new_require, 1), encoding='utf-8')
