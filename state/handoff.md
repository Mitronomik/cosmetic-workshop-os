# Handoff

Updated: `2026-08-09`

Current lifecycle authority: `docs/current-lifecycle.md`. Accepted Restore decisions: ADR 0016 and ADR 0018. Closed A plan: `docs/c4-ii-a-implementation-slices.md`. Current B plan: `docs/c4-ii-b-implementation-slices.md`.

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

## B1 merged baseline

```text
reviewed head — 27726058af4f373ab65225ecf4d1a945f1c53067
merge/new main — 5e13b50f1918dacbf8d54066c9156942a9adb895
full backend+launcher — 2480/2480 PASS
external exact-head substitution smoke — PASS
independent audit — P0=0 / P1=0 / P2=0
```

## Authorized work — B2 only

```text
browser/session
→ POST /v1/restore/execute(request_id, command_seq, generation)
→ exact-next command consumed
→ require current accepted generation + retained A1 proof
→ copy proof/path into one launcher-private in-memory intent
→ invalidate retained source authority
→ state = restoring
→ HTTP returns without running C4-I
→ launcher main runtime takes intent
→ ProofBoundRestoreRequest
→ existing C4-I execute_restore
→ ordinary backend restart handoff if safe
→ pathless final control state
```

The control plane stays alive on the same ephemeral port while ordinary backend is intentionally stopped/restarted. Heartbeat/state remain serviceable. Cancel/session expiry after execution acceptance cannot cancel destructive Restore.

B2 must change the launcher runtime wait model so an intentional C4-I stop of the original backend is not treated as launcher termination and cannot cause cleanup to kill a newly restarted backend.

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

B3 remains not authorized. B2 requires focused exact-head tests, full regressions, external isolated process smoke and independent `P0=0/P1=0/P2=0`, then merge and separate lifecycle closure before any B3 authorization.
