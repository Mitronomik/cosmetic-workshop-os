# Handoff

Updated: `2026-08-11`

Current lifecycle authority: `docs/current-lifecycle.md`. Restore authority: ADR 0016 and ADR 0018. Current B plan: `docs/c4-ii-b-implementation-slices.md`.

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

## Closed B2 baseline

```text
PR #184 reviewed head — 1ae8bfcdf0f1f1798ce85eac0931925d029379c4
PR #184 merge/new main — 266c50a77e5f353fa77701cb854629a99460667f
```

Verification: focused B2/runtime 37 PASS; launcher 636; backend 1867; total 2503/2503; frontend Restore 16/16; anti-hang PASS without manual interruption; corrected external process smoke PASS; independent `P0=0/P1=0/P2=0`; final exact-head/clean-worktree PASS.

## Next implementation — B3

```text
accepted
→ explicit human confirmation
→ local dismiss OR execute
→ POST /v1/restore/execute
   exact request_id + command_seq + generation
→ B2 authority boundary
→ restoring / restore_completed / restore_failed / restore_blocked
```

The execute pending replay must preserve the **same request ID, command sequence and generation**. Browser never gets source path/proof/digest.

B3 is frontend-only. No launcher/backend changes, `/v1/restore/confirm`, destructive cancellation, C4-II-C or C4-III work are authorized.
