# Progress

Updated: `2026-08-09`

## Completed / merged baseline

- C1/C2 completed; C3 completed, merged, exact-head verified and hardened.
- C4-I — `DONE — MERGED AND EXACT-HEAD VERIFIED`.
- A1/A2/A3/A4 — merged and exact-head verified.
- PR #181 merged as `beae1407af270ad1c800c308ea7907750430eb1d`, closing C4-II-A and authorizing B1.
- PR #182 reviewed `27726058af4f373ab65225ecf4d1a945f1c53067`, merged as `5e13b50f1918dacbf8d54066c9156942a9adb895`; B1 exact-head verified and closed by current lifecycle changeset.
- Searchable history and five exact pre-compaction snapshots remain protected.

## Current lifecycle

```text
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
C4-II-B2 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## B1 final evidence

- focused B1: 10/10;
- Restore privacy: 10/10;
- full backend+launcher: 2480/2480;
- external exact-head source substitution smoke: PASS;
- source changed before `prepared`, no operation record/safety copy/working DB mutation;
- exact repository status/head remained clean;
- independent audit: `P0=0/P1=0/P2=0`.

## B2 authorization

B2 is now the only authorized implementation slice. Exact semantics are fixed in `docs/c4-ii-b-implementation-slices.md`:

```text
/v1/restore/execute
→ exact request_id + command_seq + generation
→ one-shot accepted authority transfer
→ launcher-private RestoreExecutionIntent
→ main launcher runtime
→ ProofBoundRestoreRequest
→ existing C4-I execute_restore
→ ordinary backend restart/result handoff
```

The same control plane remains alive through the destructive interval; session expiry cannot cancel already accepted C4-I execution. Frontend remains unchanged until B3.

## Still blocked

```text
C4-II-B3 — not authorized
C4-II-C — not authorized
C4-III — not authorized
```

## Open product obligations

- implement and exact-head verify B2;
- lifecycle-close B2 before any B3 authorization;
- later B3 explicit destructive confirmation;
- later C4-II-C outcome/restart/support UX;
- C4-III end-to-end Restore closure;
- macOS packaging/update/install verification/full release-candidate smoke.
