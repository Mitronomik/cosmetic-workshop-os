# Packaging

Status: **CURRENT — D3 IMPLEMENTED; D4 DECIDED; D4-A NEXT**
Updated: `2026-08-13`

The exact pre-CR-013 packaging document is preserved in `docs/history/d4-pre-decision/packaging.md`.

## Current lifecycle

```text
D3 — macOS package MVP — IMPLEMENTED
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — AUTHORIZED — IMPLEMENTATION NOT STARTED
D4-A — Version identity and compatibility preflight — AUTHORIZED NEXT — NOT IMPLEMENTED
D4-B — Safe migration execution and durable UpdateLog — PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED
D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

## D3 baseline

The package remains `CosmeticWorkshopOS.app` distributed in `CosmeticWorkshopOS-mac.zip`, with a bundled Python runtime, built frontend, existing launcher/backend architecture and user data outside the application package. D4 does not introduce another desktop shell.

## D4 manual update model

D4 is safe manual package replacement:

```text
close old package
→ keep it temporarily
→ place/open newer package
→ use the same external user-data directory
→ compatibility preflight
→ safe schema migration when required
→ successful ordinary startup
→ only then consider discarding the previous package
```

The previous package is **not** a guaranteed rollback after the database update commit point. An older package must independently prove the canonical database lineage is compatible; otherwise it fails closed before mutation.

## Version projection contract

D4-A introduces one repository-owned build-time product version. `Info.plist`, `package-runtime.json` and backend/UI runtime status are projections of that same source. They are not independent version authorities.

The historical mutable database `app.version` placeholder is not used to decide package identity or compatibility.

## Packaged failure UX

The existing Finder-visible fixed-message mechanism remains the packaging boundary for fatal pre-browser failures. D4-C may extend it with bounded update/migration failure categories. It must not expose paths, tracebacks, SQL, operation IDs or migration internals.

## Explicit non-goals

CR-013 does not authorize:

- auto-update download;
- internet update checking;
- GitHub Releases integration;
- release channels/background updater;
- installer redesign;
- signing/notarization;
- DMG;
- App Store;
- sandbox migration;
- D5;
- release readiness;
- Electron/Tauri/pywebview/new desktop shell.
