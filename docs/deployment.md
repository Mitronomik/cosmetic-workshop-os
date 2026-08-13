# Deployment

Status: **CURRENT — LOCAL-FIRST TOPOLOGY UNCHANGED**
Updated: `2026-08-13`

The exact pre-CR-013 document is preserved in `docs/history/d4-pre-decision/deployment.md`.

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

## Topology

CR-013 changes **no deployment topology**.

The product remains:

```text
packaged local application
→ existing launcher
→ local backend on loopback
→ built frontend/local browser UI
→ SQLite + artifacts in external user-data directory
```

Ordinary work requires no cloud service and no mandatory internet connection.

D4 adds a startup safety contract, not a deployment tier. The newer package reuses the same external user-data directory and must preflight schema compatibility before any migration or ordinary backend start.

The future D4-B migration stage and durable UpdateLog remain under the external user-data boundary and outside the package. They do not create a server deployment, cloud sync or multi-user topology.

## Authorization boundary

Only D4-A is authorized next. D4-B/C/D and D5 remain gated. No signing, notarization, DMG, App Store, release channel, updater downloader, cloud deployment or cloud sync is authorized by CR-013.
