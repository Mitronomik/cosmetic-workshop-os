# Handoff

Updated: `2026-08-09`

Current lifecycle authority: `docs/current-lifecycle.md`. Accepted Restore decisions: ADR 0016 and ADR 0018. Closed A plan: `docs/c4-ii-a-implementation-slices.md`. Current B plan: `docs/c4-ii-b-implementation-slices.md`.

## Current lifecycle

```text
PR #183 — MERGED — B2 AUTHORIZED
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
C4-II-B2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Merged B2 authorization baseline

```text
PR #183 reviewed head — fa922f56c19a2dd33b6307ae0a197d476f91489b
PR #183 merge/new main — 4617b8c436eaa510fd545d863346595e2d808ea7
```

B1 remains closed on PR #182 with full regression `2480/2480`, external exact-head source-substitution smoke PASS and independent `P0=0 / P1=0 / P2=0`.

## Current B2 implementation

```text
browser/session
→ POST /v1/restore/execute(request_id, command_seq, generation)
→ exact-next command consumed before business preconditions
→ require current accepted control generation + retained A1 proof
→ copy proof/path into one launcher-private in-memory intent
→ invalidate retained source authority
→ state = restoring
→ HTTP returns without running C4-I
→ launcher main runtime owner loop takes intent
→ ProofBoundRestoreRequest
→ existing C4-I execute_restore
→ canonical ordinary-backend restart handoff if safe
→ pathless final control state
```

The control plane stays alive on the same ephemeral port while the ordinary backend is intentionally stopped/restarted. Heartbeat/state remain serviceable. Select/cancel/second execute during `restoring` consume valid sequences but cannot cancel or duplicate destructive Restore. Browser-session expiry invalidates authentication but cannot cancel accepted C4-I or overwrite launcher-owned final state.

Control generation and retained-proof generation are intentionally separate domains. Only the accepted control snapshot generation crosses HTTP; source authority comes from the current launcher-private proof.

The runtime now uses a bounded main-owner loop rather than one stale initial `process.wait()`. C4-I still owns backend stop/exclusion and all destructive semantics. Restart uses existing `BackendProcessOwner` against canonical `context.database_path`; restart failure leaves C4-I truth unchanged and returns to safe maintenance exclusion before `restore_blocked`.

## Verification still required

Do not present B2 as closed until all of these are real exact-head evidence:

- lifecycle checker + syntax;
- focused B2 tests;
- A1/A2/A3/A4/B1/C4-I regressions;
- full backend+launcher regression;
- external isolated process smoke on the published PR head;
- clean exact head/worktree;
- independent `P0=0/P1=0/P2=0` audit.

## Not B2

- browser confirmation/button or frontend parser changes;
- `/v1/restore/confirm`;
- browser path/proof/digest;
- C4-I/staging/safety-copy/replacement/rollback duplication;
- destructive cancellation;
- persistent execution state beyond existing C4-I durable record;
- Restore AuditLog changes;
- dependency/packaging redesign;
- B3/C4-II-C/C4-III authorization.

## Successor gate

B3 remains not authorized. After B2 exact-head evidence is green and the B2 PR merges, a separate lifecycle closure is still required before any B3 authorization.
