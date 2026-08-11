# C4-II-B implementation authorization and slice plan

Status: **CLOSED NORMATIVE IMPLEMENTATION PLAN**
Updated: `2026-08-11`

This document records the closed C4-II-B slices. ADR 0016 and ADR 0018 remain authoritative.

## Current slice status

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

## Closed B1/B2/B3

B1 binds launcher-private source proof to C4-I intake. B2 owns one-shot launcher execution authority and safe ordinary-backend restart handoff. B3 owns explicit browser destructive confirmation, exact pending execute replay and pathless restoring/final-state parsing.

B3 final reviewed head `316358c65a851b46090121c7a6bc877b980176ba`; merge `b9ca2bd77d5f2be0ba406e9669c18f74e1955725`.

Accepted B3 evidence remains: frontend build PASS; focused Restore 30/30 PASS; browser smoke v4 PASS; final independent P0=0/P1=0/P2=0; final no-change gate PASS. The historical P1=1 pre-fix audit remains preserved in project history.

## Successor

PR #187 reviewed head `48e245811af706bb666620c6dda8033ff200967a` merged as `7a746fbf98f50682b509c40a06335a2157f1a7b7` and authorized C4-II-C.

C4-II-C is now implemented in the current changeset but not closed. It may change presentation only and must not reopen B1/B2/B3 authority, contract/runtime, launcher/backend, main/navigation or ADRs.

C4-III remains PLANNED — NOT AUTHORIZED. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
