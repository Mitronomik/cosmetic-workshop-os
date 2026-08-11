# Restore interaction and validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-11`

Normative sources: ADR 0016 for destructive Restore; ADR 0018 for launcher control/picker/exact-run browser session; current lifecycle plus the A/B slice plans for implementation status.

## Current lifecycle

```text
PR #185 — MERGED — B3 AUTHORIZED
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
C4-II-B3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed A1→A4 architecture

```text
browser SPA /backups/restore
  ├── ordinary business API → FastAPI backend
  └── Restore control → launcher-owned 127.0.0.1:<ephemeral>
                         → A2 action/session coordinator
                           ├── A3 native picker
                           └── A1 validation worker
                         → B2 queue-only destructive command
                         → main launcher runtime owner path
                         → C4-I destructive engine
```

Browser owns presentation only. Launcher owns loopback control, picker, selected absolute path, retained proof and all destructive authority.

## Closed B1 proof seam

B1 is merged and exact-head verified. Base `RestoreRequest` remains selected-source-only. Launcher-private `ProofBoundRestoreRequest` adds `ExpectedSourceProof(SourceIdentity, SHA-256)` only.

```text
A1 retained source path + SourceIdentity + SHA-256
→ ProofBoundRestoreRequest
→ C4-I open_selected_source(...)
→ bind_expected_source_proof(...) on HeldSource H
→ H.identity + revalidate + self-containment
→ H.digest() full SHA-256 + exact byte count
→ revalidate + self-containment again
→ exact same H
→ unchanged C4-I stage_source(..., H)
```

Any mismatch fails before `prepared` with fixed `SOURCE_CHANGED`. No path/proof crosses browser control.

## B2 closure — closed coordinator seam

PR #184 reviewed exact head `1ae8bfcdf0f1f1798ce85eac0931925d029379c4` merged as `266c50a77e5f353fa77701cb854629a99460667f`.

Accepted closure evidence includes focused B2/runtime **37 PASS**, launcher **636 PASS**, backend **1867 PASS**, full backend+launcher **2503/2503 PASS**, frontend Restore **16/16 PASS**, autonomous anti-hang PASS, corrected external exact-head isolated process smoke PASS, independent **P0=0 / P1=0 / P2=0**, and final no-change exact-head/clean-worktree PASS.

B2 exposes one exact-run authenticated destructive command:

```text
POST /v1/restore/execute
```

with exact request keys:

```text
request_id
command_seq
generation
```

`generation` is only the accepted control selection generation and stale-view guard. Browser never sends source path, proof, digest or operation identity. A1 retained-proof generation remains a separate launcher-internal domain.

### One-shot authority transfer

```text
authenticate exact run
→ validate exact schema/request ID/command sequence
→ consume exactly-next sequence before business preconditions
→ require state == accepted
→ require submitted generation == current accepted control generation
→ require current launcher-private retained A1 proof
→ copy retained source path + identity + digest into one in-memory intent
→ invalidate retained candidate authority immediately
→ state = restoring
→ queue one RestoreExecutionIntent
→ return safe command reply
```

HTTP/session workers do not execute C4-I. The launcher main runtime consumes the intent and calls existing `execute_restore(..., LauncherLifecycleContext)` exactly once. The same control plane remains alive on the same ephemeral port while the ordinary backend is stopped/restarted.

During `restoring`, heartbeat/state remain serviceable, there is no destructive cancel command, session expiry cannot cancel accepted C4-I, and launcher-owned final result publication may complete after browser authentication expires.

B2 launcher states are exactly:

```text
restoring
restore_completed
restore_failed
restore_blocked
```

The snapshot stays pathless and exposes no source path, staged path, operation ID, durable record content, SQL, migration IDs or traceback.

### Backend restart handoff

Existing C4-I remains the owner of backend stop/exclusion and all destructive work. When C4-I permits normal startup, launcher restart uses canonical `context.database_path` and the existing owned-process lock/socket handshake. Restart failure does not reinterpret C4-I truth and returns to safe maintenance exclusion before `restore_blocked`.

## B3 implementation changeset — explicit browser confirmation

PR #185 reviewed B3 authorization head `f206cf4896abcc7e8ecd0266cacd3f8a6d89e22c` and merged as `f6589bdd7c403b6d400e3f5b7a0daea75b14632a`. The current changeset implements only that frontend authorization.

```text
accepted candidate
→ browser shows explicit destructive confirmation dialog
→ local dismiss/Escape OR explicit destructive confirm
→ runtime creates one pending execute command
   request_id + command_seq + accepted generation
→ same-tab history replay stores only safe pending command metadata
→ POST /v1/restore/execute
→ B2 remains launcher authority-transfer boundary
→ browser polls pathless restoring/final state
```

No `/v1/restore/confirm` endpoint is introduced.

### Browser state parsing

B3 TypeScript parsing now accepts the four B2 execution states already owned by the launcher:

```text
restoring
restore_completed
restore_failed
restore_blocked
```

Unknown states continue to fail closed. The snapshot DTO exact-key shape is unchanged.

### Execute generation ownership

The DOM/confirmation layer does not submit or choose `generation` directly.

`RestoreControlRuntime.execute()` reads only the current parsed snapshot. It proceeds only when that snapshot is `accepted` and has a positive integer generation. That generation is copied into the pending execute command.

Therefore the browser UI cannot use an arbitrary stale generation injected by a button/data attribute or by a caller outside the runtime state machine.

### Exact destructive replay

Replay state remains version `1` for backward compatibility.

The pending representation is now discriminated:

```text
select/cancel pending:
  action
  requestId
  commandSeq

execute pending:
  action
  requestId
  commandSeq
  generation
```

The historical select/cancel shape remains valid unchanged.

The execute parser requires exact fields and a valid positive generation. Extra source/path/proof/digest fields make replay state invalid.

On ambiguous network result:

```text
first execute
→ persist pending execute before fetch
→ network outcome unknown
→ keep exact pending request
→ user chooses retry
→ resend same request_id
          same command_seq
          same generation
```

No second request ID or sequence is allocated while a pending execute exists.

### Explicit confirmation UX

The destructive action is only available for the current `accepted` candidate when the exact-run session is ready, protocol-safe and has no pending command.

Opening the confirmation is a local UI state transition. The dialog is a native semantic `<dialog>` and is tied to the accepted snapshot generation.

The confirmation:

- identifies only the safe escaped display filename;
- explains that current workshop data will be replaced by the chosen backup;
- explains that the application may be temporarily unavailable;
- explains that the existing Restore engine automatically creates a protective copy of the current database before replacement;
- says that already started Restore cannot be cancelled from this screen;
- focuses the safe `Вернуться` action first;
- keeps `Восстановить данные` as an explicit danger action.

Dismiss button and Escape are local-only. They send neither execute nor `/v1/restore/cancel`.

If the runtime snapshot, accepted generation, availability or pending state changes while confirmation is open, the local confirmation authority is discarded.

### Duplicate-submit prevention

`runtime.execute()` synchronously persists the pending command before awaiting the network request. A second execute call therefore sees the pending command and cannot allocate a second sequence or second destructive request.

This protects both rapid repeated clicks and programmatic near-simultaneous calls.

### `restoring` presentation

While launcher state is `restoring`:

- browser continues polling `/v1/state` on the launcher control port;
- select/cancel/re-confirm controls are not shown;
- no destructive cancel exists;
- no fake percentage or internal phase is displayed;
- safe launcher-provided message may be presented;
- generic network guidance avoids claiming that working data was unchanged after destructive execute may have started.

### Final B2 state presentation

`restore_completed`, `restore_failed` and `restore_blocked` are no longer protocol errors. B3 minimally presents the safe launcher-provided state/message and does not infer durable phases or technical recovery facts.

C4-II-C still owns richer truthful completion, rollback, restart and support-assisted UX.

### B3 implementation surface

```text
frontend/src/restore-control-contract.ts
frontend/src/restore-control-runtime.ts
frontend/src/restore-control-presentation.ts
frontend/src/restore-control-entry.ts
frontend/test/restore-control.test.mjs
frontend/test/restore-control-races.test.mjs
```

`frontend/src/main.ts` and `frontend/src/app-navigation-routes.ts` remain unchanged. No launcher/backend/migration/dependency/package resource is changed.

## B3 verification still required

This document records implementation presence, not PASS claims. Before B3 may merge, the published exact head still requires frontend build, focused Restore tests, A4 regressions, lifecycle checker, desktop/narrow-screen/keyboard confirmation smoke, exact replay/duplicate-submit proof, clean head/worktree and independent `P0=0 / P1=0 / P2=0` audit.

C4-II-C and C4-III remain separately blocked. Product Restore remains **NOT IMPLEMENTED**.