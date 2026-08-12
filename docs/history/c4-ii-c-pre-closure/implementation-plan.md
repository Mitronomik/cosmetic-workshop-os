# cosmetic-workshop-os — Active implementation plan

Updated: `2026-08-11`

## Current lifecycle

```text
PR #187 — MERGED — C4-II-C AUTHORIZATION BASELINE
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
C4-II-C — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed predecessor

PR #187 reviewed exact head `48e245811af706bb666620c6dda8033ff200967a` and merged as `7a746fbf98f50682b509c40a06335a2157f1a7b7`, closing B3 lifecycle and authorizing C4-II-C only.

B3 evidence remains accepted: frontend build PASS; focused Restore 30/30 PASS; browser smoke v4 PASS; final independent audit P0=0/P1=0/P2=0; final no-change gate PASS.

## Current implementation window

### C4-II-C — Truthful Restore completion/recovery/restart/support UX

Status: **IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED**.

Goal:

```text
existing restoring/final launcher state
→ truthful human-readable result
→ safe next action
→ restart/recovery/support guidance where appropriate
```

Production change:

```text
frontend/src/restore-control-presentation.ts
```

Focused tests:

```text
frontend/test/restore-control-races.test.mjs
```

Expected focused Restore control suite on the published C4-II-C implementation head: **34 tests / 34 pass / 0 fail**.

`frontend/src/restore-control-contract.ts remains closed`.
`frontend/src/restore-control-runtime.ts` remains closed.
`frontend/src/restore-control-entry.ts` remains closed in this implementation.
Launcher/backend/main/navigation/migrations/dependencies/package resources/ADR 0016/ADR 0018 remain closed.

### Required product truth

- completed → explicit success + ordinary navigation;
- failed → ordinary app availability without rollback/unchanged-data inference;
- blocked → restart/help guidance, no normal-work navigation;
- post-execute session/network uncertainty without a final launcher result → unknown result, no inferred success/failure/rollback/unchanged data;
- authenticated final launcher state remains authoritative even when same-tab replay metadata is missing; replay loss disables further Restore commands but does not erase the final result;
- exact replay of an ambiguous pending execute remains the same command only, never a new sequence or blind destructive retry.

### Non-goals

No new launcher state, endpoint, DTO field, browser source/path authority, operation ID, durable phase timeline, destructive cancel, automatic Restore retry, backend Restore ownership, packaging redesign or C4-III work.

### Required verification

Run exact-head frontend build, focused Restore tests (**expected 34 tests / 34 pass / 0 fail**), lifecycle checker, desktop+narrow+keyboard browser smoke, closed-blob review, clean head/worktree and independent P0/P1/P2 audit before merge.

C4-III remains not authorized. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
