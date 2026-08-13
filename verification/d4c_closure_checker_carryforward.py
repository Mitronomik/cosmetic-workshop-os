from pathlib import Path

p = Path("scripts/check_documentation_lifecycle.py")
t = p.read_text(encoding="utf-8")
anchor = '    "D4 — Update safety — IN PROGRESS — D4-C IMPLEMENTED, VERIFICATION PENDING",\n'
extra = '''    "D4 — Update safety — IN PROGRESS — D4-B IMPLEMENTED, VERIFICATION PENDING",
    "D4-B — Safe migration execution and durable UpdateLog — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING",
    "D4 — Update safety — IN PROGRESS — D4-A IMPLEMENTED, VERIFICATION PENDING",
    "D4-A — Version identity and compatibility preflight — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING",
    "D4-B — Safe migration execution and durable UpdateLog — PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED",
'''
if t.count(anchor) != 1:
    raise SystemExit("D4-C closure checker carry-forward anchor mismatch")
t = t.replace(anchor, anchor + extra, 1)
p.write_text(t, encoding="utf-8")
