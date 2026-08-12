# Change Requests

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

## Restore decisions

CR-011 remains **ACCEPTED**. ADR 0018 remains normative for launcher-owned loopback control, picker/session security and browser path privacy. ADR 0016 remains normative for destructive Restore durable truth.

PR #187 merged as `7a746fbf98f50682b509c40a06335a2157f1a7b7` and authorized C4-II-C only.

## Current implementation

C4-II-C implements the already-authorized **frontend-only** truthful completion/recovery/restart/support UX. No new Change Request is needed because it does not change launcher state, DTOs, endpoints, source authority or destructive semantics.

If implementation later appears to require a new launcher state, endpoint, DTO field, browser filesystem authority, durable phase, backend behavior or new destructive command, STOP and open a new architecture/lifecycle decision.

C4-III remains PLANNED — NOT AUTHORIZED. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
