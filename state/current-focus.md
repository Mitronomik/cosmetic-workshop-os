# Current Focus — C4-II-B2 launcher destructive coordinator

Updated: `2026-08-09`

## Merged baseline

```text
PR #182 reviewed B1 head — 27726058af4f373ab65225ecf4d1a945f1c53067
PR #182 merge/new main — 5e13b50f1918dacbf8d54066c9156942a9adb895
```

## Current lifecycle

```text
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## B1 closure

B1 exact head `27726058...` passed focused tests, privacy, full backend+launcher `2480/2480`, external exact-head substitution smoke and independent `P0=0/P1=0/P2=0`, then merged as `5e13b50...`.

The base request remains selected-source-only; B1 proof binding uses the same C4-I `HeldSource` descriptor and fails before `prepared` on mismatch.

## Current work — B2 only

B2 adds one authenticated `/v1/restore/execute` command. It consumes the current accepted control generation and current launcher-private retained proof into exactly one in-memory `RestoreExecutionIntent`, invalidates that source authority, and returns without running destructive work in the HTTP/session worker.

The launcher main runtime owns the intent and calls existing C4-I with `ProofBoundRestoreRequest`. The same control plane stays alive while C4-I stops the ordinary backend. The main runtime then performs the safe ordinary-backend restart handoff and publishes a pathless final control state.

## Hard seams

No browser confirmation/UI, no `/v1/restore/confirm`, no browser path/proof, no second Restore engine, no phase/recovery/safety-copy/AuditLog redesign, no new dependency/port/service, and no B3 authorization.
