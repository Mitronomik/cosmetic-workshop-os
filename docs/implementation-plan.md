# cosmetic-workshop-os — Active implementation plan

Project: `cosmetic-workshop-os`
Client-facing name: **Мастерская косметолога**
Status: **active current implementation sequence**
Updated: `2026-08-09`

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

## Merged baseline

```text
PR #182 reviewed B1 head — 27726058af4f373ab65225ecf4d1a945f1c53067
PR #182 merge/new main — 5e13b50f1918dacbf8d54066c9156942a9adb895
PR #183 reviewed B2-authorization head — fa922f56c19a2dd33b6307ae0a197d476f91489b
PR #183 merge/new main — 4617b8c436eaa510fd545d863346595e2d808ea7
```

## Current implementation changeset — C4-II-B2

B2 implements only the launcher destructive coordinator/control command defined in `docs/c4-ii-b-implementation-slices.md`.

Implemented flow:

```text
POST /v1/restore/execute
  exact body: request_id + command_seq + generation
→ authenticated/session/replay checks
→ consume exactly-next sequence before business preconditions
→ require current accepted control generation + current retained A1 proof
→ copy launcher-private path + ExpectedSourceProof into one launcher-private RestoreExecutionIntent
→ atomically invalidate retained source authority
→ return safe `restoring` reply; HTTP/session workers never call `execute_restore(...)`
→ launcher main runtime consumes intent synchronously
→ ProofBoundRestoreRequest(retained source path, ExpectedSourceProof)
→ existing execute_restore(..., LauncherLifecycleContext)
→ existing C4-I owns backend stop/exclusion + all destructive semantics
→ main runtime performs ordinary-backend restart handoff when safe
→ publish safe pathless final control state
```

## Implemented B2 seams

- `/v1/restore/execute` is the only new destructive control command.
- Browser body carries exactly `request_id + command_seq + generation`; no path, proof, digest, operation ID or target path crosses HTTP.
- `generation` is a stale-view guard only; A1 retained-proof generation remains a separate internal domain.
- Command sequence/retry rules remain ADR 0018 exact-next and idempotent.
- Accepted source authority is one-shot and invalidated immediately when intent is accepted.
- HTTP/session workers never call `execute_restore(...)`.
- `RestoreExecutionIntent` is in-memory launcher-private state only.
- Main launcher runtime, not an HTTP/background destructive worker, consumes the intent.
- C4-I remains the only destructive Restore engine.
- The same control plane stays alive while the ordinary backend is intentionally stopped/restarted.
- Heartbeat/state remain responsive during `restoring`.
- Select/cancel/second execute during `restoring` consume their valid sequence and return `restore_in_progress` without cancelling or duplicating C4-I.
- Session expiry invalidates browser authentication but cannot cancel accepted destructive C4-I or overwrite launcher-owned result state.
- Main runtime replaces the stale one-shot `process.wait()` lifetime assumption with one bounded owner loop.
- Backend restart uses canonical `context.database_path` through existing `BackendProcessOwner` lock/socket handshake.
- If C4-I does not permit normal startup, no ordinary backend starts.
- Backend restart failure does not rewrite or roll back the C4-I result; safe maintenance exclusion is re-established before `restore_blocked`.
- B2 adds only `restoring`, `restore_completed`, `restore_failed`, `restore_blocked` control states.
- frontend remains byte-identical and B3 remains not authorized.

## Protected implementation boundaries

The B2 implementation gate keeps these merged boundaries byte-identical:

```text
launcher/restore/contracts.py
launcher/restore/engine.py
launcher/restore/source_proof.py
launcher/restore/staging.py
launcher/restore/validation_session.py
launcher/restore/validation_scratch.py
launcher/restore/context.py
launcher/restore/verification.py
launcher/restore/macos_picker.py
launcher/restore/browser_handoff.py
launcher/tests/test_restore_source_proof_binding.py
frontend/src/main.ts
frontend/src/app-navigation-routes.ts
frontend/src/restore-control-contract.ts
frontend/src/restore-control-runtime.ts
frontend/src/restore-control-presentation.ts
frontend/src/restore-control-entry.ts
```

No ordinary FastAPI backend, migration, dependency or packaging resource is in B2 scope.

## Required B2 proof before merge

The current changeset is **not yet closed**. It still requires actual exact-head evidence for:

1. lifecycle checker and Python syntax;
2. focused B2 HTTP/schema/replay/authority-transfer tests;
3. restoring-state and session-expiry tests;
4. main-runtime/C4-I/restart-result tests;
5. existing A1/A2/A3/A4/B1/C4-I regressions;
6. full backend+launcher regression;
7. frontend byte-identity and normal unchanged frontend regression where repository policy requires it;
8. external exact-head isolated process smoke proving command → real backend stop → B1 re-proof → C4-I → restart/result handoff on the same control-plane port;
9. clean exact head/worktree;
10. independent `P0=0/P1=0/P2=0` audit.

Do not record any of these as PASS until actually run against the published PR head.

## Forbidden scope

No B3 browser confirmation/UI, no `/v1/restore/confirm`, no ordinary FastAPI Restore mutation, no second Restore engine, no phase/recovery redesign, no Restore AuditLog change, no new dependency, no packaging redesign, no cloud sync/OCR/roles/multiuser/advanced analytics.

## Next action

Publish B2 as one bounded Draft PR → run focused/regression exact-head tests → run external isolated process smoke → independent audit → merge only when all required evidence is green → separate B2 lifecycle closure before any B3 authorization.
