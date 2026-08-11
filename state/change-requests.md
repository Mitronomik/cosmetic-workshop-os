# Change Requests

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

## Restore decisions

CR-011 remains **ACCEPTED**. ADR 0018 remains normative for launcher-owned loopback Restore control, native source selection, exact-run session security, replay ordering and browser path privacy. ADR 0016 remains normative for destructive Restore safety/durable truth.

No new Change Request is required to close merged B3: PR #186 implemented the already-authorized B3 contract and passed final exact-head verification.

## Current authorization

**C4-II-C — Truthful Restore completion/recovery/restart/support UX** is AUTHORIZED NEXT — NOT IMPLEMENTED as a bounded **frontend-only** successor over the merged B2/B3 state contract.

This authorization does not reopen CR-011/ADR 0018 or ADR 0016. No new launcher state, no new control endpoint, no browser filesystem authority, no destructive retry, no destructive cancel, no new DTO field, no operation ID/durable phase in browser, and no backend Restore endpoint are authorized.

If implementation discovers that any such change is necessary, stop and open a new architecture/lifecycle decision instead of widening C4-II-C.

C4-III remains PLANNED — NOT AUTHORIZED. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
