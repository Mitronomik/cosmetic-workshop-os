# Deployment

Status: **CURRENT — LOCAL-FIRST TOPOLOGY UNCHANGED**
Updated: `2026-08-13`

The exact pre-CR-013 document is preserved in `docs/history/d4-pre-decision/deployment.md`.

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

Closed D4-B implements the migration stage and durable UpdateLog under the existing external user-data boundary. It adds no service, cloud dependency or second launcher topology; exact PR-head and merged-head Level-5 verification passed.

## Authorization boundary

D4 is closed with no deployment-topology change. CR-014 authorizes D5 only as documentation + exact-package assisted-install rehearsal over the same local topology. Release/distribution infrastructure, cloud work and runtime topology changes remain unauthorized.

## CR-015 lifecycle repair boundary

CR-015 changes no deployment topology: the application remains local-first, the browser remains the UI, and user data remain external to the `.app`. The only authorized runtime change is the native macOS application lifecycle wrapper required for responsive Dock Quit and repeat launch. No cloud, remote management or release-channel work is authorized.

## CR-015 closure deployment truth

The merged native lifecycle repair changes no deployment topology. The browser remains the product UI, the backend remains local, and user data remain external to the `.app`. The fixed package now participates correctly in the macOS application lifecycle for ordinary Quit/restart. D5 still requires a fresh human clean-Mac rehearsal; no remote-management or release topology is authorized.
