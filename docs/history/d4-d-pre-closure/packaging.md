# Packaging

Status: **CURRENT — D3 IMPLEMENTED; D4-A/B/C CLOSED; D4-D AUTHORIZED NEXT**
Updated: `2026-08-13`

The exact pre-CR-013 packaging document is preserved in `docs/history/d4-pre-decision/packaging.md`.

## Current lifecycle

```text
D3 — macOS package MVP — IMPLEMENTED
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C DONE; D4-D AUTHORIZED NEXT
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
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

D4-C closure authorizes D4-D only. It does not authorize auto-update download, internet update checking, GitHub Releases integration, release channels, installer redesign, signing/notarization, DMG, App Store, sandbox migration, D5 or release readiness.
