# Packaging

Status: **CURRENT — D3 IMPLEMENTED; D4 CLOSED; D5 DECIDED AND AUTHORIZED NEXT; RELEASE NOT CLAIMED**
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
D5 — Remote install checklist — BLOCKER FIXED — FRESH HUMAN REHEARSAL REQUIRED
CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX
D5 blocker fix — Native macOS application lifecycle — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D5 verification — AUTOMATED BLOCKER FIX VERIFIED — FULL D5 PASS NOT YET CLAIMED
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015
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

D4 is closed and final exact-package verified. CR-014 authorizes D5 only to document and rehearse assisted installation of the existing ZIP/.app. It does not authorize package-runtime redesign, auto-update/download, internet update checking, GitHub Releases, release channels, signing/notarization, DMG/PKG, App Store, sandbox migration, Phase 12 or release readiness.

## CR-015 native macOS lifecycle blocker

The first clean-Mac D5 human rehearsal exposed that the current shell/Python `CFBundleExecutable` does not provide a healthy native macOS Dock/Quit lifecycle even though the local browser product runtime itself starts. CR-015 / ADR 0022 authorizes a minimal AppKit lifecycle executable around the existing packaged bootstrap only. This is a product-lifecycle repair, not signing/notarization, DMG/PKG, App Store packaging or a new desktop UI framework.

## CR-015 implementation closure

The native lifecycle repair is merged and exact-package verified. `CosmeticWorkshopOS.app` now has a Mach-O/AppKit `CFBundleExecutable`, while `CosmeticWorkshopOSRuntime` retains the existing self-contained shell/Python isolation path. Verified head `d7f95141e5f41c7a806c3fafb71e942fe5892dd8`, merge `c38940349a80d345f3e833b61e4bf4e5e761c0eb`, run `31780899805`, exact ZIP SHA-256 `85f993a93082c4b3a36771318cf8c0c3abf02be56b1374a32a62d1a6b9279ee6`. This closes only the lifecycle blocker; signing/notarization and release distribution remain out of scope.
