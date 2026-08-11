# Restore interaction and validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-11`

Normative sources: ADR 0016 for destructive Restore; ADR 0018 for launcher control/picker/exact-run browser session; current lifecycle plus the A/B slice plans for implementation status.

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

The earlier eight-hour manually interrupted run remains invalid evidence. The first smoke runner remains `INCONCLUSIVE RUNNER` because bootstrap was consumed before the production A4 handoff.

B2 adds one exact-run authenticated destructive command:

```text
POST /v1/restore/execute
```

Exact request keys:

```text
request_id
command_seq
generation
```

`generation` is only the safe accepted control selection generation. Browser never sends source path, proof, digest or operation identity. A1 retained-proof generation remains an independent launcher-internal generation domain and is not numerically compared with the browser/control generation.

### One-shot authority transfer

Under the control-session lock:

```text
authenticate exact run
→ validate exact schema/request ID/command sequence
→ consume exactly-next sequence before business preconditions
→ require state == accepted
→ require submitted generation == current accepted control generation
→ require no active picker/validation or destructive execution
→ require current launcher-private retained A1 proof
→ copy retained source path + identity + digest into one in-memory intent
→ invalidate retained candidate authority immediately
→ state = restoring
→ queue one RestoreExecutionIntent
→ return safe command reply
```

Retry of the same highest command sequence/request ID returns cached safe state and never queues/executes again. Stale/future/conflicting sequences remain refused exactly as ADR 0018 requires. A valid business refusal still consumes its exactly-next sequence.

### Destructive work does not run in HTTP/session worker

The HTTP boundary is only an authenticated command/queue boundary. It does not call C4-I directly and does not import the C4-I engine as an HTTP execution path.

The **main launcher runtime loop** takes the queued intent and synchronously constructs:

```text
ProofBoundRestoreRequest(
    selected_source=<launcher-private retained path>,
    expected_source_proof=ExpectedSourceProof(<retained identity>, <retained SHA-256>)
)
```

It then calls existing `execute_restore(..., LauncherLifecycleContext)` exactly once.

The runtime loop checks for a queued intent before treating the original backend process exit as launcher termination. No generic supervisor or destructive background worker is introduced.

### Control-plane lifetime during destructive Restore

The same loopback control plane remains alive and bound to the same ephemeral port while C4-I stops the ordinary backend and while ordinary-backend restart is attempted.

During `restoring`:

- authenticated heartbeat and `GET /v1/state` remain serviceable;
- select/cancel/second execute consume their otherwise-valid next sequence and return `restore_in_progress`;
- there is no destructive cancel command;
- browser/tab close or session expiry does not cancel C4-I after the execution intent was accepted;
- expiry invalidates browser authentication and stale candidate authority but does not overwrite launcher-owned `restoring` or final execution state;
- launcher-owned final result publication may complete after browser authentication expired;
- the control plane is not rebound and no new bootstrap capability is generated mid-execution.

### B2 control result states

B2 extends launcher control state with:

```text
restoring
restore_completed
restore_failed
restore_blocked
```

These states were not added to frontend in B2. The pre-B3 frontend remains byte-identical in this closure/authorization change.

The snapshot stays pathless. It exposes no source path, staged path, operation ID, durable record content, SQL, migration IDs or traceback.

### Backend restart handoff

Existing C4-I remains the owner of backend stop/exclusion and all destructive work. B2 does not pre-stop or duplicate that logic.

When C4-I returns with `normal_startup_allowed=True`, the main launcher runtime requires the retained maintenance lease, releases it immediately before `BackendProcessOwner.start(...)`, and restarts ordinary service on canonical `context.database_path` through the existing lock/socket handshake.

Only after that backend is proved ready may control state become:

- `restore_completed` for successful completed C4-I truth;
- `restore_failed` for a safe unsuccessful/aborted/rolled-back C4-I result with ordinary service restored.

If restart fails:

- C4-I truth is not reinterpreted or rolled back;
- maintenance exclusion is re-acquired/retained when no backend owns the workspace;
- `restore_blocked` is published with fixed safe guidance;
- durable Restore truth remains untouched.

When C4-I does not allow normal startup, or verification hits the existing retryable backend-port condition, B2 starts no ordinary backend and publishes `restore_blocked`. Startup recovery on the next launcher run remains authoritative.

## B2 non-goals — closed evidence

Merged B2 did not implement browser destructive confirmation/button, `/v1/restore/confirm`, frontend parser/presentation changes, browser-supplied source path/proof/digest, a second Restore engine, destructive cancellation after execution begins, phase/recovery/safety-copy/replacement/AuditLog redesign, persistence of proof/intent/result/session token, or any new dependency/helper executable/port/packaging architecture.

## Authorized B3 browser confirmation contract

B3 is frontend-only except focused frontend tests and lifecycle/checker/status docs.

```text
accepted candidate
→ explicit confirmation dialog
→ local dismiss OR execute confirm
→ POST /v1/restore/execute(request_id, command_seq, generation)
→ B2 authority-transfer boundary
→ pathless restoring/final launcher state
```

B3 may parse exactly `restoring`, `restore_completed`, `restore_failed`, `restore_blocked`. Unknown states remain fail-closed. The launcher snapshot shape remains unchanged.

The confirmation is presentation only. It adds no `/v1/restore/confirm` endpoint and never grants browser filesystem authority. Filename remains display-only; `generation` remains a stale-view guard.

### Exact destructive replay

Current select/cancel replay persists only action, request ID and command sequence. Execute additionally requires the accepted generation.

Pending execute must retain:
- action = `execute`;
- same request ID;
- same command sequence;
- accepted generation.

An ambiguous transport retry resends the **same request ID, same command sequence and accepted generation**. It must not allocate a new request ID or sequence. Existing select/cancel replay remains backward-safe. No source path/proof/digest may enter `sessionStorage` or `history.state`.

### UX boundary

Only an `accepted` candidate may open destructive confirmation. Dismissing the dialog is local and sends no `/v1/restore/cancel`. Repeated confirmation cannot produce multiple execute commands.

The dialog uses the safe display filename and explains in plain language that current workshop data will be replaced, the application may be temporarily unavailable, and existing Restore safety logic creates a protective copy before replacement. It uses existing danger visual language and accessible dialog/focus semantics.

`restoring` shows a non-technical in-progress state, disables duplicate confirmation, offers no destructive cancellation and invents no fake phase/percentage. Heartbeat/state polling continues on the launcher control port.

Final B2 states may display only the safe launcher-provided message. C4-II-C remains responsible for richer truthful completion, rollback, restart and support-assisted presentation; B3 must not infer durable truth.

## Authorized B3 implementation surface

Primarily:

```text
frontend/src/restore-control-contract.ts
frontend/src/main.ts                 # minimal wiring only
frontend/src/<focused Restore B3 modules if needed>
frontend/tests/<focused Restore B3 tests>
docs/state/checker files required for implementation status
```

No launcher/backend changes are authorized. If implementation discovers that launcher/backend behavior must change, stop and open an architecture/lifecycle question instead of widening B3.

## Verification required for future B3

Future B3 must prove contract parsing, exact execute schema/privacy, explicit confirmation, double-submit protection, replay of the exact request ID/sequence/generation, restoring-state behavior, minimal final-state presentation, existing A4 bootstrap/session/select/cancel/replay regression, and ordinary navigation regression.

C4-II-C and C4-III remain separately blocked. Product Restore remains **NOT IMPLEMENTED**.
