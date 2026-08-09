# Restore interaction and validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-09`

Normative sources: ADR 0016 for destructive Restore; ADR 0018 for launcher control/picker/exact-run browser session; current lifecycle plus the A/B slice plans for implementation status.

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

## Closed A1→A4 architecture

```text
browser SPA /backups/restore
  ├── ordinary business API → FastAPI backend
  └── Restore control → launcher-owned 127.0.0.1:<ephemeral>
                         → A2 action/session coordinator
                           ├── A3 native picker
                           └── A1 validation worker
                         → C4-I shared intake/staging/validation
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

## Authorized B2 coordinator seam

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

`generation` is only the safe control selection generation. Browser never sends source path, proof, digest or operation identity.

### One-shot authority transfer

Under the control-session lock:

```text
authenticate exact run
→ validate exact schema/request ID/command sequence
→ consume exactly-next sequence before business preconditions
→ require state == accepted
→ require submitted generation == current accepted generation
→ require no active picker/validation or destructive execution
→ require current launcher-private retained A1 proof
→ copy retained source path + identity + digest into one in-memory intent
→ invalidate retained candidate authority immediately
→ state = restoring
→ queue one RestoreExecutionIntent
→ return safe command reply
```

Retry of the same highest command sequence/request ID returns cached safe state and never queues/executes again. Stale/future/conflicting sequences remain refused exactly as ADR 0018 requires.

### Destructive work does not run in HTTP/session worker

The HTTP boundary is only an authenticated command/queue boundary. It must never call C4-I directly.

The **main launcher runtime loop** takes the queued intent and constructs:

```text
ProofBoundRestoreRequest(
    selected_source=<launcher-private retained path>,
    expected_source_proof=ExpectedSourceProof(<retained identity>, <retained SHA-256>)
)
```

It then calls existing `execute_restore(..., LauncherLifecycleContext)` exactly once.

This keeps process ownership coherent: the same launcher owner that normally tracks the backend also owns the intentional C4-I stop/restart transition. An HTTP worker may not compete with the main runtime's backend wait/cleanup path.

### Control-plane lifetime during destructive Restore

The same loopback control plane remains alive and bound to the same ephemeral port while C4-I stops the ordinary backend.

During `restoring`:

- authenticated heartbeat and `GET /v1/state` remain serviceable;
- select/cancel/second execute consume their otherwise-valid next sequence and return `restore_in_progress`;
- there is no destructive cancel command;
- browser/tab close or session expiry does not cancel C4-I after the execution intent was accepted;
- expiry invalidates browser authentication/source authority but launcher-owned execution continues;
- the control plane is not rebound and no new bootstrap capability is generated mid-execution.

### B2 control result states

B2 may extend launcher control state with:

```text
restoring
restore_completed
restore_failed
restore_blocked
```

These states are not added to frontend in B2. Current A4 frontend remains unchanged and therefore cannot initiate B2. Future B3/C must update TypeScript parsing/presentation before the product browser can use this destructive path.

The snapshot stays pathless. It may expose only fixed safe message/failure categories already suitable for presentation; it must not expose source path, staged path, operation ID, durable record content, SQL, migration IDs or traceback.

### Backend restart handoff

Existing C4-I remains the owner of backend stop/exclusion and all destructive work. B2 does not pre-stop/duplicate that logic.

When C4-I returns with `normal_startup_allowed=True`, the main launcher runtime attempts to restart ordinary service on canonical `context.database_path` through `BackendProcessOwner.start(...)`, with the accepted lock/socket handshake.

Only after that backend is proved ready may control state become `restore_completed` or `restore_failed`.

If restart fails:

- do not reinterpret or roll back the C4-I result;
- ensure maintenance exclusion is held when no backend owns the workspace;
- publish `restore_blocked` with fixed safe restart guidance;
- leave durable Restore truth untouched.

When C4-I does not allow normal startup, or verification hits the existing retryable backend-port condition, B2 starts no ordinary backend and publishes `restore_blocked`. Startup recovery on the next launcher run remains authoritative.

### Launcher runtime loop

B2 must replace the assumption that one initial `process.wait()` equals the launcher lifetime. The launcher must distinguish an ordinary backend crash from the intentional C4-I stop and then continue with the newly restarted owned backend when one exists.

No process is found or signalled by port/name/PID pattern. Existing `BackendProcessOwner` remains authority.

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

## Future B3/C

B3 remains blocked until B2 is merged and exact-head verified. B3 will extend the browser contract and add explicit human destructive confirmation before sending `/v1/restore/execute`.

C4-II-C remains separately blocked and owns full truthful completion/rollback/restart/support-assisted user presentation. B2 only provides the safe launcher/control handoff needed for that later UI.
