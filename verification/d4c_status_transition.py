from pathlib import Path

CODE = "adfe37a3f68a545635f173c22d4710eacde86e74"
OLD_D4 = "D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C AUTHORIZED NEXT"
NEW_D4 = "D4 — Update safety — IN PROGRESS — D4-C IMPLEMENTED, VERIFICATION PENDING"
OLD_C = "D4-C — User-facing update status and packaged failure UX — AUTHORIZED NEXT — NOT IMPLEMENTED"
NEW_C = "D4-C — User-facing update status and packaged failure UX — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING"
SURFACES = (
    "README.md", "docs/current-lifecycle.md", "docs/implementation-plan.md",
    "docs/packaging.md", "docs/deployment.md", "state/current-focus.md",
    "state/progress.md", "state/handoff.md", "state/change-requests.md",
)

for name in SURFACES:
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    if OLD_D4 not in text or OLD_C not in text:
        raise SystemExit(f"{name}: old D4-C lifecycle truth missing")
    path.write_text(text.replace(OLD_D4, NEW_D4).replace(OLD_C, NEW_C), encoding="utf-8")

Path("state/current-focus.md").write_text(f"""# Current focus

Updated: `2026-08-13`

## Current lifecycle

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
{NEW_D4}
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
{NEW_C}
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

## Current task

**Verify the D4-C implementation only; do not start D4-D.**

Implementation code commit: `{CODE}`. Verify the final published PR head with full regression, lifecycle integrity, frontend build, real macOS package and exact-package D4-C smoke.

D4-C remains presentation-only: no browser update authority, no technical update dashboard, no raw update metadata, exactly two packaged update-failure outcomes, and no protected Restore changes.

## Do not start

- D4-D;
- D5;
- auto-update/download;
- signing/notarization/DMG/App Store;
- release readiness;
- Restore changes.
""", encoding="utf-8")
