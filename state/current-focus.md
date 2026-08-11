# Current Focus — C4-II-B3 browser confirmation implementation

Updated: `2026-08-11`

## Current lifecycle

```text
PR #185 — MERGED — B3 AUTHORIZED
PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED
PR #183 — MERGED — B2 AUTHORIZATION BASELINE
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
C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed baseline

PR #184 reviewed B2 head `1ae8bfcdf0f1f1798ce85eac0931925d029379c4` merged as `266c50a77e5f353fa77701cb854629a99460667f`.

PR #185 reviewed B3-authorization head `f206cf4896abcc7e8ecd0266cacd3f8a6d89e22c` merged as `f6589bdd7c403b6d400e3f5b7a0daea75b14632a`.

## Current work — B3 verification only

The B3 frontend seam is present:

- explicit confirmation only from current `accepted` snapshot;
- local dismiss/Escape sends no execute/cancel;
- exact execute body `request_id + command_seq + generation`;
- generation sourced only from parsed accepted snapshot;
- exact ambiguous retry with the same request ID, command sequence and generation;
- backward-safe select/cancel replay;
- duplicate execute guard before HTTP;
- `restoring` polling without select/cancel/reconfirm/fake progress;
- minimal safe final state presentation;
- `main.ts` unchanged;
- no launcher/backend/dependency/migration/package-resource change.

Current work is now evidence gathering. Do not claim B3 closed or tested until exact-head build/tests/smoke/audit are observed.

## Hard seams

No `/v1/restore/confirm`, no browser source path/proof/digest, no destructive cancel, no launcher/backend Restore change, no C4-II-C/C4-III authorization.