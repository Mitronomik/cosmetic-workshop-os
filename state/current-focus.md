# Current Focus — C4-II-C truthful Restore results implementation

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

## Closed baseline

PR #187 reviewed head `48e245811af706bb666620c6dda8033ff200967a` merged as `7a746fbf98f50682b509c40a06335a2157f1a7b7` and authorized C4-II-C only.

B3 remains exact-head verified and closed.

## Current work

**C4-II-C — Truthful Restore completion/recovery/restart/support UX** is implemented in the current changeset but is not lifecycle-closed.

Production scope is only `frontend/src/restore-control-presentation.ts`; focused result-state tests are in `frontend/test/restore-control-races.test.mjs`.

Implemented semantics:

- completed → success + safe ordinary navigation;
- failed → no rollback/unchanged-data inference;
- blocked → restart/help, no normal-work navigation;
- execute/restoring connection uncertainty → explicit unknown result, no false final truth;
- existing exact ambiguous replay remains the same previous command only.

Closed launcher/backend/contract/runtime/entry/main/navigation seams must remain byte-identical.

C4-III remains PLANNED — NOT AUTHORIZED. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
