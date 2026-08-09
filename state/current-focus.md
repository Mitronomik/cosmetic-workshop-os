# Current Focus — C4-II-B1 retained source-proof binding

Updated: `2026-08-09`

## Merged baseline

```text
PR #181 reviewed B1-authorization head — d2549cd9be2b60c5aee2479050e05a6ad8530c6c
PR #181 merge/new main — beae1407af270ad1c800c308ea7907750430eb1d
```

## Current lifecycle

```text
PR #181 — MERGED — B1 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B2 — PLANNED — NOT AUTHORIZED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Current work — B1 only

B1 preserves base `RestoreRequest` as selected-source-only and adds launcher-private `ProofBoundRestoreRequest(RestoreRequest)` carrying only `ExpectedSourceProof(SourceIdentity, SHA-256)`. The existing C4-I source is opened once; `bind_expected_source_proof(...)` proves identity, descriptor/path stability, self-containment, full held-descriptor digest and exact byte count before `_execute_with_source(...)`. The exact same `HeldSource` is then passed into unchanged `stage_source(...)`.

Mismatch returns fixed `SOURCE_CHANGED` guidance before `prepared`, safety copy or working-database mutation. Legacy C4-I callers continue to use base `RestoreRequest` unchanged.

`launcher/restore/staging.py`, A1 and all frontend/A2/A3/A4 code remain unchanged. The proof subtype introduces no destructive/application-owned path.

## Required closure evidence

Focused B1 tests; base-request contract regression; legacy C4-I regression; closed A1/A2/A3/A4 regressions; full backend+launcher regression; external exact-head isolated B1 smoke; clean worktree/head; independent P0/P1/P2 audit.

## Hard seams

No browser change, no new control endpoint, no destructive confirmation/coordinator, no duplicate staging/validation, no safety-copy/replacement/recovery redesign and no Restore AuditLog change. B2/B3 remain separately not authorized.
