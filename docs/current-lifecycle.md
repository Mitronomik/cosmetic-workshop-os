# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-13`

For historical pre-D4 decision state, see `docs/history/d4-pre-decision/`. The exact pre-decision `docs/current-lifecycle.md` is preserved there byte-identically from base `dc2301f7d4e101ad0fba851325dae9274f02da0c`.

## Authority

- ADR 0016 remains authoritative for destructive Restore.
- ADR 0018 remains authoritative for Restore interaction/validation session semantics.
- ADR 0019 remains authoritative for the bounded D3 macOS package decision.
- ADR 0020 is authoritative for D4 Update Safety once CR-013 is merged.
- `docs/roadmap.md` remains the product-scope source for D4 and D5.
- `docs/domain-model-d4-update-safety.md` is the bounded D4 companion clarification for the conceptual UpdateLog/AppSettings/BackupRecord fields.

## Current lifecycle

```text
PR #193 — MERGED — C4-III RESTORE LIFECYCLE CLOSURE
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED

CR-012 — ACCEPTED — D3 MACOS PACKAGE MVP AUTHORIZATION
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

## What CR-013 decided

D4 is a manual package-replacement safety programme. It does not add an updater downloader or release/distribution system.

The accepted control model is:

```text
read-only compatibility preflight
→ verified before_migration backup
→ consistent SQLite migration stage
→ migrate and verify stage
→ atomic database commit
→ durable external UpdateLog
→ ordinary backend startup
```

The ordered `schema_migrations` lineage remains the schema source of truth. Existing `app_settings["app.version"]` is historical only. D4-A will introduce one repository-owned application-version source and propagate one effective runtime version.

An existing database that is newer than the running application, or whose lineage is unsupported/unreadable, fails closed **before mutation**. A pre-existing SQLite file without recognizable lineage is not treated as a fresh database.

The previous application package is not a generic rollback after the database commit point. Any older package must independently pass the same lineage compatibility gate.

## Authorization boundary

Only D4-A may begin after this decision is merged.

D4-A may implement:

- one canonical app-version identity and generated package/runtime projections;
- ordinary-startup read-only lineage compatibility preflight;
- fail-closed newer/unsupported lineage refusal;
- focused backend/launcher/package tests.

D4-A may **not** implement:

- staged migration execution;
- UpdateLog persistence;
- frontend update status;
- new packaged update-failure UI;
- D4-B/C/D;
- D5;
- signing, notarization, DMG, App Store, updater/download or release readiness.

## Closed Restore boundary

Restore remains closed. CR-013 does not amend its twelve-phase state machine, source selection, source proof, browser control plane, backend handshake, replacement/recovery semantics or protected production files.

If D4 implementation requires changing a closed Restore production boundary, work must stop for a separate decision.
