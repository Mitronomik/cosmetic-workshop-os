# Restore interaction and validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-09`

Normative sources: ADR 0016 for destructive Restore; ADR 0018 for launcher control/picker/exact-run browser session; current lifecycle plus the A/B slice plans for implementation status.

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

## Implemented B2 coordinator seam

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

The runtime loop checks for a queued intent before treating the original backend process exit as launcher termination. That is the bounded ownership change required for C4-I's intentional stop; no generic supervisor or destructive background worker is introduced.

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

These states are not added to frontend in B2. Current A4 frontend remains byte-identical and therefore cannot initiate or present B2 execution. Future B3/C must update TypeScript parsing/presentation before the product browser can use this destructive path.

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

## B2 non-goals

B2 does not authorize or implement:

- browser destructive confirmation/button;
- `/v1/restore/confirm`;
- frontend parser/presentation changes;
- browser-supplied source path/proof/digest;
- a second Restore engine;
- destructive cancellation after execution begins;
- phase/recovery/safety-copy/replacement/AuditLog redesign;
- persistence of proof/intent/result/session token;
- new dependency, helper executable, port or packaging architecture.

## Verification status and future B3/C

The B2 code exists in the current changeset but is **not yet lifecycle-closed**. Focused/regression exact-head tests, external isolated process smoke and independent audit remain required before merge.

B3 remains blocked until B2 is merged, exact-head verified and separately lifecycle-closed. B3 will extend the browser contract and add explicit human destructive confirmation before sending `/v1/restore/execute`.

C4-II-C remains separately blocked and owns full truthful completion/rollback/restart/support-assisted user presentation. B2 only provides the safe launcher/control handoff needed for that later UI.
