# cosmetic-workshop-os — Active implementation plan

Updated: `2026-08-11`

## Current lifecycle

```text
PR #186 — MERGED — C4-II-B3 EXACT-HEAD VERIFIED
PR #185 — MERGED — B3 AUTHORIZATION BASELINE
PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED
PR #183 — MERGED — B2 AUTHORIZATION BASELINE
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-C — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed Restore implementation through C4-II-B

PR #186 final reviewed head: `316358c65a851b46090121c7a6bc877b980176ba`.
PR #186 merge/new main: `b9ca2bd77d5f2be0ba406e9669c18f74e1955725`.

C4-II-B1, B2 and B3 are now closed. C4-I remains the sole destructive engine; B2 owns launcher execution authority; B3 owns browser explicit confirmation and exact replay.

Final B3 evidence: lifecycle/build PASS; focused Restore **30/30 PASS**; external browser smoke v4 PASS; final independent P0=0/P1=0/P2=0; final no-change gate PASS. The earlier P1 audit failure on `de827c5789f165949d0dbcd4fbbda4f5d368d71f` is historical and was corrected before merge.

## Current implementation window

### C4-II-C — Truthful Restore completion/recovery/restart/support UX

Status: **AUTHORIZED NEXT — NOT IMPLEMENTED**.

Goal:

```text
existing restoring/final launcher state
→ truthful human-readable result
→ safe next action
→ restart/recovery/support guidance where appropriate
```

This slice is **frontend-only**.

Primary expected production surface:

```text
frontend/src/restore-control-presentation.ts
```

Optional bounded wiring only if necessary:

```text
frontend/src/restore-control-entry.ts
```

Focused tests may update:

```text
frontend/test/restore-control.test.mjs
frontend/test/restore-control-races.test.mjs
```

`frontend/src/restore-control-contract.ts remains closed`.
`frontend/src/restore-control-runtime.ts` remains closed.
`launcher/**`, `backend/**`, `frontend/src/main.ts`, `frontend/src/app-navigation-routes.ts`, migrations, dependencies, package resources, ADR 0016 and ADR 0018 remain closed.

If implementation appears to require a new launcher state, new DTO field, new control endpoint, backend behavior, source/path data, operation ID, durable phase data or another authority transfer: STOP and open an architecture/lifecycle question.

Hard prohibitions: no new launcher state, no new control endpoint, no browser filesystem authority, no destructive retry, no destructive cancel, no automatic Restore retry, no durable phase timeline, no technical diagnostics console, no packaging redesign, no C4-III work.

### Required product truth

- `restore_completed`: clear success only within merged B2 backend-ready semantics.
- `restore_failed`: do not infer rollback, unchanged data, restored old data or no mutation; no blind destructive retry.
- `restore_blocked`: ordinary work is not safe in the current run; provide restart/recovery/support guidance and no normal-work/destructive-retry affordance.
- session/network uncertainty after execute may have begun must remain uncertainty, not inferred success/failure/rollback/unchanged-data truth.

### Required verification for the future implementation PR

Small bounded PR, exact-head frontend build and focused tests, desktop+narrow+keyboard browser smoke, truthfulness tests for all three final states and network/session uncertainty, changed-path review, clean head/worktree, independent P0/P1/P2 audit, then merge only after all evidence is green.

C4-III remains not authorized. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
