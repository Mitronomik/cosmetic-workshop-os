# Packaging

Status: **CURRENT — D3 IMPLEMENTED; D4 CLOSED; D5 INSTALL DOCS IMPLEMENTED; D5 NOT LIFECYCLE-CLOSED; RELEASE NOT CLAIMED**
Updated: `2026-08-13`

The exact pre-CR-013 packaging document is preserved in `docs/history/d4-pre-decision/packaging.md`.

## Current lifecycle

```text
D3 — macOS package MVP — IMPLEMENTED
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED
CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT
D5 — Remote install checklist — IMPLEMENTED — NOT LIFECYCLE-CLOSED
D5 verification — AUTOMATED EXACT-PACKAGE + HUMAN CLEAN-MAC/CLEAN-PROFILE EVIDENCE REQUIRED
D5 lifecycle closure — NOT COMPLETED
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014
Product release readiness — NOT CLAIMED
```

## D3 baseline

The package remains `CosmeticWorkshopOS.app` distributed in `CosmeticWorkshopOS-mac.zip`, with a bundled Python runtime, built frontend, existing launcher/backend architecture and user data outside the application package. D4 does not introduce another desktop shell.

## D4-A version projection contract

`backend/VERSION` is now the one editable repository-owned build-time product version. D4-A accepts a numeric `major.minor.patch` identity token only; it never orders application versions to decide schema compatibility.

Generated/read-only projections:

```text
backend/VERSION
→ backend pyproject dynamic version
→ Info.plist CFBundleShortVersionString / CFBundleVersion
→ package-runtime.json app_version
→ effective backend Settings/status version
```

The source `backend/VERSION` file is deliberately **not copied into the packaged application root**. Inside a built package the validated `package-runtime.json` value is the effective runtime identity. A present but malformed package manifest fails closed instead of falling back to a developer checkout value.

`scripts/verify_product_version.py` runs during package assembly and rejects a mismatch among `backend/VERSION`, backend package metadata configuration, Info.plist and package-runtime.json.

The historical mutable database `app.version` placeholder is not used to decide package identity or compatibility.

## D4 manual update model

D4 remains safe manual package replacement. D4-A supplies the closed compatibility gate; D4-B owns staged migration and UpdateLog; D4-C adds only bounded read-only status/failure presentation on top of that startup truth.

The previous package is **not** a guaranteed rollback after the database update commit point. An older package must independently prove the canonical database lineage is compatible; otherwise it fails closed before mutation.

## Packaged failure UX

D4-C extends the existing Finder-visible fixed-message catalogue with two update outcomes only: stopped before canonical DB replacement, or completion cannot be confirmed automatically. Messages are fixed, non-technical and never interpolate exception text, paths or migration internals.

## Explicit non-goals

D4 is closed and final exact-package verified. D5 now implements only documentation/rehearsal material for assisted installation of the existing ZIP/.app; verification and lifecycle closure remain separate. It does not authorize package-runtime redesign, auto-update/download, internet update checking, GitHub Releases, release channels, signing/notarization, DMG/PKG, App Store, sandbox migration, Phase 12 or release readiness.
