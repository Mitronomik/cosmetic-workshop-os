# Current Focus — C4-II-B3 authorization ready

Updated: `2026-08-11`

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

## Closed baseline

PR #184 reviewed B2 head `1ae8bfcdf0f1f1798ce85eac0931925d029379c4` merged as `266c50a77e5f353fa77701cb854629a99460667f`.

B2 exact-head verification is closed: 37 focused PASS, launcher 636 PASS, backend 1867 PASS, total 2503/2503, frontend Restore 16/16, autonomous anti-hang PASS, corrected external process smoke PASS, independent `P0=0/P1=0/P2=0`, final clean-head PASS.

## Current work — B3 only

B3 is frontend-only explicit destructive confirmation. It must send the already-merged B2 execute body exactly as `request_id + command_seq + generation`.

An ambiguous execute retry must preserve the **same request ID, command sequence and generation**. No filesystem authority may cross or persist in browser state.

No launcher/backend change, `/v1/restore/confirm`, destructive cancel, C4-II-C or C4-III work is authorized.
