# Current Focus — C4-II-C authorization after B3 closure

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

## Closed predecessor

PR #186 final reviewed head `316358c65a851b46090121c7a6bc877b980176ba` merged as `b9ca2bd77d5f2be0ba406e9669c18f74e1955725`.

Accepted B3 evidence: lifecycle/build PASS, 30/30 focused Restore tests, browser smoke v4 PASS, final independent P0=0/P1=0/P2=0, and final no-change gate PASS. The earlier P1=1 audit on `de827c5789f165949d0dbcd4fbbda4f5d368d71f` remains historical evidence and was corrected before merge.

## Current authorized work

**C4-II-C — Truthful Restore completion/recovery/restart/support UX** is the only authorized next implementation slice and is **frontend-only**.

Primary implementation surface: `frontend/src/restore-control-presentation.ts`; bounded `restore-control-entry.ts` wiring only if needed.

No new launcher state, no new control endpoint, no browser filesystem authority, no destructive retry, no destructive cancel. Closed launcher/backend/contract/runtime/main-shell seams must remain byte-identical.

The slice must distinguish `restore_completed`, `restore_failed`, `restore_blocked` and **session/network uncertainty** truthfully. Do not infer rollback, unchanged data or durable phases in browser.

C4-III remains PLANNED — NOT AUTHORIZED. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
