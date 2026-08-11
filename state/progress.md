# Progress

Updated: `2026-08-11`

## Completed / merged baseline

- C1/C2 completed; C3 completed, merged, exact-head verified and hardened.
- C4-I — `DONE — MERGED AND EXACT-HEAD VERIFIED`.
- A1/A2/A3/A4 — merged and exact-head verified.
- B1 — merged and exact-head verified on PR #182.
- B2 — reviewed head `1ae8bfcdf0f1f1798ce85eac0931925d029379c4`, merged as `266c50a77e5f353fa77701cb854629a99460667f`, exact-head verified and closed.
- B2 accepted evidence: focused 37 PASS; launcher 636; backend 1867; total 2503/2503; frontend Restore 16/16; anti-hang PASS; corrected external process smoke PASS; independent `P0=0/P1=0/P2=0`; final clean-head PASS.

## Current lifecycle

```text
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
C4-II-B3 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Authorized next work

B3 explicit browser destructive confirmation only:
- parse the four merged B2 execution states;
- require explicit confirmation for current `accepted`;
- call only `/v1/restore/execute`;
- exact body `request_id + command_seq + generation`;
- replay ambiguous execute with the **same request ID, command sequence and generation**;
- persist no filesystem authority;
- disable duplicate/cancel affordances during `restoring`;
- keep C4-II-C result/recovery UX out of B3.

## Still blocked

```text
C4-II-C — not authorized
C4-III — not authorized
```
