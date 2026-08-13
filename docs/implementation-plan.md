# Implementation plan

Status: **CURRENT**
Updated: `2026-08-13`

The exact pre-CR-013 plan is preserved in `docs/history/d4-pre-decision/implementation-plan.md` from base `dc2301f7d4e101ad0fba851325dae9274f02da0c`.

## Current lifecycle

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
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

Normative D4 decision: `docs/decisions/0020-d4-update-safety-contract.md`.

## D4 programme

### D4-A — Version identity and compatibility preflight

**AUTHORIZED NEXT — NOT IMPLEMENTED**.

Goal: establish immutable application identity and stop incompatible databases before any startup mutation.

Scope:

- introduce one canonical repository-owned build-time product-version source;
- derive package metadata/runtime version projections from it;
- make backend read-only Settings/status expose that same effective runtime version;
- keep historical DB `app.version` non-authoritative;
- reuse/generalize the existing read-only migration-lineage classifier for ordinary startup;
- classify absent DB, current known lineage, supported older prefix, newer lineage and unsupported/unreadable lineage;
- fail closed before backup/migration/backend/browser for incompatible existing databases;
- focused backend, launcher and packaged-runtime tests.

Non-goals:

- no staged migration redesign;
- no durable UpdateLog;
- no frontend update presentation;
- no new Finder update-failure category yet;
- no D4-B/C/D;
- no Restore change;
- no updater/download/signing/notarization/DMG/App Store/D5.

Acceptance gate for D4-A:

- exact-head tests pass;
- newer/unsupported existing lineage is proven pre-mutation;
- first-run path applies only when canonical DB does not exist;
- package and source-tree runtime resolve the same product version identity;
- protected Restore blobs remain byte-identical;
- independent review/verification passes before D4-B is authorized.

### D4-B — Safe migration execution and durable UpdateLog

**PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED**.

Planned architecture from ADR 0020:

```text
consistent before_migration backup
→ consistent runner-owned migration stage
→ migrate only stage
→ verify target lineage
→ atomic canonical publication
→ durable external UpdateLog
```

The stage must be created through SQLite-consistent snapshot semantics, not raw file copy. Interruption must never cause automatic blind destructive retry.

### D4-C — User-facing update status and packaged failure UX

**PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED**.

Planned product surface:

- small read-only human status in existing Settings/status;
- fixed Russian packaged failure copy before ordinary browser startup;
- no technical update admin panel.

### D4-D — Exact-package update verification and lifecycle closure

**PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED**.

Will verify manual package replacement, older-schema migration, failure/interruption boundaries, repeated launch, downgrade refusal, UpdateLog truth and cleanup on the exact packaged artifact. Only then may D4 lifecycle closure be considered.

## D5

`D5 — Remote install checklist` remains **NOT AUTHORIZED BY CR-013**.

## Release boundary

D4 is update safety, not release distribution. Product release readiness remains **NOT CLAIMED**. Signing, notarization, DMG, App Store, release channels, auto-download and internet update checking require separate authorization.
