# Current Focus — C4-II-B2 launcher destructive coordinator

Updated: `2026-08-09`

## Merged baseline

```text
PR #182 reviewed B1 head — 27726058af4f373ab65225ecf4d1a945f1c53067
PR #182 merge/new main — 5e13b50f1918dacbf8d54066c9156942a9adb895
PR #183 reviewed B2-authorization head — fa922f56c19a2dd33b6307ae0a197d476f91489b
PR #183 merge/new main — 4617b8c436eaa510fd545d863346595e2d808ea7
```

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

## Current work — B2 verification only

The B2 implementation changeset contains the authorized launcher-only bridge:

```text
POST /v1/restore/execute(request_id, command_seq, generation)
→ exact-next sequence consumed before business preconditions
→ current accepted control generation + current retained A1 proof
→ one-shot launcher-private RestoreExecutionIntent
→ retained authority invalidated
→ pathless restoring reply
→ HTTP/session returns without C4-I
→ main launcher runtime owner loop takes intent
→ ProofBoundRestoreRequest
→ existing C4-I execute_restore
→ existing C4-I owns destructive semantics
→ canonical owned-backend restart/result handoff
```

The same control plane remains alive on the same ephemeral port. Session expiry cannot cancel accepted destructive execution or overwrite launcher-owned final state. Frontend remains byte-identical.

Current work is now evidence gathering: focused/regression exact-head tests, external isolated process smoke, clean-head proof and independent audit. No test or smoke PASS is claimed here until actually run.

## Hard seams

No browser confirmation/UI, no `/v1/restore/confirm`, no browser path/proof/digest, no second Restore engine, no B1/C4-I phase/recovery/safety-copy/AuditLog redesign, no ordinary backend/migration/dependency/package-resource change, and no B3/C4-II-C/C4-III authorization.
