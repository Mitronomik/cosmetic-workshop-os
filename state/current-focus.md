# Current Focus — C4-III Restore end-to-end verification

Updated: `2026-08-11`

## Current lifecycle

```text
PR #188 — MERGED — C4-II-C EXACT-HEAD VERIFIED
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
C4-II-C — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-III — AUTHORIZED NEXT — NOT IMPLEMENTED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed baseline

PR #188 reviewed exact C4-II-C head `1df21915fdcf4a708dc778a0e762d64830b5b880` and merged as `6294f0044c792ced3ac56d213ea5333e33062f12` at `2026-08-11T17:25:11Z`.

C4-II-C is closed on lifecycle PASS, frontend build PASS, focused Restore 34/34 PASS, browser smoke v5.4 PASS, fresh independent audit P0=0/P1=0/P2=0 and final no-change exact-head gate PASS.

## Current work

**C4-III — Restore end-to-end verification and lifecycle closure** is the only authorized next Restore slice. It is not implemented yet.

Verification must cover current-schema + supported older-schema Restore, rejection, interruption, rollback, repeated launch/startup recovery, source immutability, mandatory safety-copy retention and end-to-end lifecycle closure.

Production Restore authority is closed. Do not change launcher/backend/contract/runtime/entry/presentation/main/navigation/ADRs in C4-III. Tests, isolated smoke runners and verification/lifecycle documentation may change. Any product defect requires a separate bounded fix PR.

Restore remains NOT IMPLEMENTED until C4-III closes. Product release readiness remains NOT CLAIMED.
