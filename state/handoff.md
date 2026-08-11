# Handoff

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

PR #187 reviewed head `48e245811af706bb666620c6dda8033ff200967a` merged as `7a746fbf98f50682b509c40a06335a2157f1a7b7`. C4-II-C is the only authorized successor.

## Current implementation handoff

C4-II-C is present in the current changeset and remains **NOT YET CLOSED**.

Changed production file:

```text
frontend/src/restore-control-presentation.ts
```

Focused test file:

```text
frontend/test/restore-control-races.test.mjs
```

Do not change `restore-control-contract.ts`, `restore-control-runtime.ts`, `restore-control-entry.ts`, launcher/backend, main/navigation, dependencies, migrations, package resources or ADRs.

Load-bearing truth:

- `restore_completed` → success and ordinary work ready;
- `restore_failed` → ordinary work ready, but no inference that rollback happened or data is unchanged;
- `restore_blocked` → ordinary work not safely available; restart/help only, no normal navigation;
- execute/restoring session/network uncertainty → unknown result; no success/failure/rollback/unchanged-data claim;
- exact replay may repeat only the same pending execute command.

Required before merge: exact-head lifecycle/build/34 focused tests, browser smoke including narrow/keyboard and all result states, closed-blob review, independent P0/P1/P2 audit, final no-change gate.

C4-III remains blocked. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
