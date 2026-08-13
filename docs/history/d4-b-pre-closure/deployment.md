# Deployment

Status: **CURRENT — LOCAL-FIRST TOPOLOGY UNCHANGED**
Updated: `2026-08-13`

The exact pre-CR-013 document is preserved in `docs/history/d4-pre-decision/deployment.md`.

## Current lifecycle

```text
D3 — macOS package MVP — IMPLEMENTED
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — IN PROGRESS — D4-B IMPLEMENTED, VERIFICATION PENDING
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING
D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

## Topology

D4-A changes **no deployment topology**.

The product remains:

```text
packaged local application
→ existing launcher
→ local backend on loopback
→ built frontend/local browser UI
→ SQLite + artifacts in external user-data directory
```

Ordinary work requires no cloud service and no mandatory internet connection.

D4-A adds only a startup compatibility gate and product-version identity. The launcher and browser topology are unchanged; user data still lives in the same external user-data directory.

D4-B now implements the migration stage and durable UpdateLog under the existing external user-data boundary. It adds no service, cloud dependency or second launcher topology; verification and lifecycle closure are still pending.

## Authorization boundary

D4-B implementation does not authorize D4-C. D4-C/D and D5 remain unauthorized. No signing, notarization, DMG, App Store, release channel, updater downloader, cloud deployment or cloud sync is authorized by CR-013.
