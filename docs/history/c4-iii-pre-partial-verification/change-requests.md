# Change Requests

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

## Restore decisions

CR-011 remains **ACCEPTED**. ADR 0018 remains normative for launcher-owned loopback control, picker/session security and browser path privacy. ADR 0016 remains normative for destructive Restore durable truth. ADR 0017 defines C4-III as end-to-end verification and lifecycle closure.

PR #188 merged as `6294f0044c792ced3ac56d213ea5333e33062f12` and C4-II-C is now closed.

## C4-III authorization

C4-III verifies the already-decided and merged Restore architecture. No new Change Request is needed for verification-only tests, isolated smoke runners, evidence documentation or lifecycle closure.

If C4-III appears to require a new launcher state, endpoint, DTO field, browser filesystem authority, durable phase, backend behavior, destructive command, packaging architecture or other product/architecture change, STOP and open a separate decision/change request or bounded defect-fix PR as appropriate.

Restore remains NOT IMPLEMENTED until C4-III closes. Product release readiness remains NOT CLAIMED.
