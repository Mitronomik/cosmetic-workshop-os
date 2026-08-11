# C4-II-B implementation authorization and slice plan

Status: **NORMATIVE IMPLEMENTATION PLAN**
Updated: `2026-08-09`

This document slices `C4-II-B — destructive Restore confirmation and execution` without changing ADR 0016 or ADR 0018. Destructive Restore enters only through small independently reviewed PRs.

## Merged baseline

```text
PR #180 reviewed A4 head — 79c698ed76d478d608a25f4b95499ff519794228
PR #180 / A4 merge — e61d4e233c98d3c53e7749fe96ed0ee630610372
PR #181 reviewed B1-authorization head — d2549cd9be2b60c5aee2479050e05a6ad8530c6c
PR #181 / B1-authorization merge — beae1407af270ad1c800c308ea7907750430eb1d
PR #182 reviewed B1 head — 27726058af4f373ab65225ecf4d1a945f1c53067
PR #182 / B1 merge — 5e13b50f1918dacbf8d54066c9156942a9adb895
PR #183 reviewed B2-authorization head — fa922f56c19a2dd33b6307ae0a197d476f91489b
PR #183 / B2-authorization merge — 4617b8c436eaa510fd545d863346595e2d808ea7
```

## Current slice status

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

B2 code exists in the current changeset, but B2 is not closed until focused/regression exact-head tests, external isolated process smoke, independent audit, merge and a separate lifecycle-closure change are complete. B3 remains blocked throughout.

## B1 — Bind retained source proof into C4-I intake — DONE — MERGED AND EXACT-HEAD VERIFIED

B1 is closed on merged PR #182.

Accepted exact-head evidence:

- final reviewed head `27726058af4f373ab65225ecf4d1a945f1c53067`;
- merge/new main `5e13b50f1918dacbf8d54066c9156942a9adb895`;
- documentation lifecycle gate PASS;
- focused proof-binding tests 10/10;
- Restore privacy tests 10/10;
- full backend + launcher regression 2480/2480;
- external exact-head source-substitution smoke PASS;
- clean worktree/head before and after smoke;
- independent audit `P0=0 / P1=0 / P2=0`.

The closed B1 implementation keeps base `RestoreRequest` selected-source-only and uses launcher-private `ProofBoundRestoreRequest` with `ExpectedSourceProof(SourceIdentity, SHA-256)`. The expected proof is bound to the same `HeldSource` descriptor C4-I later stages, before `_execute_with_source(...)` and before `prepared`.

## B2 — Launcher destructive coordinator/control command — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED

### Goal

Add one bounded launcher-owned bridge from the existing exact-run control session into the existing C4-I engine without moving destructive work into HTTP threads, browser code or a second Restore implementation.

The implemented B2 architecture is:

```text
browser/session
→ authenticated POST /v1/restore/execute
→ atomically consume command sequence + accepted control generation
→ copy current launcher-private A1 retained proof into one in-memory execution intent
→ invalidate retained source authority immediately
→ publish safe `restoring` control state
→ enqueue exactly one launcher-private RestoreExecutionIntent
→ HTTP request returns; it does not call C4-I
→ main launcher runtime loop takes the intent
→ construct ProofBoundRestoreRequest from retained path + ExpectedSourceProof
→ existing C4-I execute_restore(request, context)
→ C4-I owns backend stop/exclusion, re-proof, staging, validation, safety copy,
   durable phases, replacement, verification and rollback
→ main launcher runtime handles ordinary-backend restart handoff
→ control session receives one safe final execution state
```

### Implementation status in this changeset

The current B2 changeset implements the bounded seam in:

```text
launcher/restore/control_protocol.py
launcher/restore/control_session.py
launcher/restore/control_plane.py
launcher/restore/execution_coordinator.py
launcher/runtime.py
launcher/tests/test_restore_execution_coordinator.py
```

The lifecycle checker is converted from a pre-B2 closure gate into a B2 implementation gate. It permits those explicitly authorized B2 seams while keeping the closed B1/C4-I/A1/A3/A4/frontend boundaries byte-pinned.

No test result is implied by this implementation status. Exact-head execution evidence remains a separate merge gate.

### Why execution belongs to the main launcher runtime

The pre-B2 runtime blocked on the ordinary backend process lifetime. C4-I intentionally stops that owned backend during destructive Restore. Running `execute_restore(...)` inside an HTTP/session worker would race the main runtime's backend wait/cleanup path and could let the launcher interpret an intentional Restore stop as application termination.

B2 therefore uses a small launcher-owned runtime owner loop that distinguishes:

- ordinary unexpected backend exit;
- a queued/active Restore transition owned by the launcher;
- the current backend process after a successful restart;
- a blocked/restart-required state in which no ordinary backend may be running.

The loop checks the one-shot Restore intent before treating the current process exit as launcher termination. The control-plane server remains on its own thread(s); destructive C4-I execution remains synchronous on the launcher runtime owner path. No generic supervisor or destructive background worker is added.

### Exact HTTP command

B2 adds exactly:

```text
POST /v1/restore/execute
```

It inherits the existing exact loopback Host/Origin/bearer-session/no-cookie/no-cache boundary.

Request body is exactly:

```json
{
  "request_id": "<128-bit-or-greater random id>",
  "command_seq": 3,
  "generation": 7
}
```

No source path, filename-as-authority, proof, SHA-256, operation ID, target path, database path, backup path, lock path or browser confirmation token may cross HTTP.

`generation` is the presentation-safe accepted control selection generation. It is a stale-view guard, not source proof. `RestoreControlSession` control generation and A1 `RetainedSourceProof.generation` remain separate domains and are not required to be numerically equal.

### Replay / one-shot semantics

All ADR 0018 sequence rules remain load-bearing.

For `/v1/restore/execute`:

1. Host/Origin/auth/body/schema/request-id/sequence syntax are validated first.
2. Exactly-next `command_seq` is atomically consumed **before** business preconditions.
3. Same highest sequence + same request ID retries return the cached safe reply and never queue/execute again.
4. Same sequence + different request ID is conflict.
5. Older sequence is stale; skipped/future sequence is rejected.
6. A valid business rejection still consumes its command sequence.
7. At most one destructive execution intent exists for one accepted source authority.

The accepted candidate authority itself is one-shot. Once B2 accepts execution, the retained A1 proof/path is copied into launcher-private intent memory and immediately invalidated in the candidate-preparation service before C4-I begins.

### Execution preconditions

Under the same control-session lock that consumes the command, B2 requires:

- current control state is `accepted`;
- submitted `generation` equals the current accepted control snapshot generation;
- no picker/validation owner is still running;
- no destructive Restore execution is already queued or active;
- current launcher-private A1 retained proof exists.

Source authority comes from the retained proof owned by the current candidate-preparation service/run; browser generation is never used as proof.

Failure is typed and safe. It queues nothing and starts no destructive work.

Required business refusal codes include:

```text
candidate_not_accepted
selection_generation_stale
restore_authority_missing
restore_in_progress
```

### Control state during B2

B2 extends the launcher control protocol with only these execution states:

```text
restoring
restore_completed
restore_failed
restore_blocked
```

They are launcher/control protocol states only. Existing A4 frontend code remains byte-identical and therefore does not initiate or present B2 execution. B3/C must later extend the TypeScript parser/presentation before the product browser can use these states.

The existing snapshot shape remains pathless. B2 does not add operation ID, durable record content, absolute path, safety-copy path, SQL, migration ID or traceback to browser state.

Safe mapping:

- `restoring` — launcher accepted the one-shot intent; destructive execution may be in progress;
- `restore_completed` — C4-I reports success and ordinary backend restart is proved ready;
- `restore_failed` — C4-I ended without success but normal startup is allowed and ordinary backend restart is proved ready;
- `restore_blocked` — ordinary startup may not safely continue, verification is retryable later, or ordinary backend restart could not be safely proved.

`message` and `failure` remain fixed non-technical vocabulary. B2 does not expose `RestoreResult.operation_id`, internal paths or durable record fields.

### Control-plane lifetime while backend is stopped

The same `RestoreControlPlane` instance remains bound to the same `127.0.0.1:<ephemeral>` address through the destructive interval and ordinary-backend restart attempt.

While state is `restoring`:

- `GET /v1/state` remains serviceable for an authenticated live session;
- heartbeat remains serviceable;
- a new select/cancel/execute mutating command consumes its valid next sequence and returns `restore_in_progress` without cancelling C4-I;
- browser/session cancellation is **not** authority to cancel destructive Restore after the execution intent was accepted;
- session expiry invalidates browser authentication and stale source authority but must not cancel, roll back, restart or overwrite the already-owned destructive execution;
- final launcher-private result publication may complete even if browser authentication expired; an expired browser simply cannot read it.

The control plane is not rebound and no second bootstrap token is created during one B2 execution.

### Main-runtime execution and backend ownership

B2 reuses existing `execute_restore(...)` and `LauncherLifecycleContext`.

The coordinator/main runtime does not pre-stop the backend. `execute_restore(...)` remains the place that calls `context.stop_backend()` and obtains the retained maintenance lease before working-database access.

The main runtime no longer uses one stale initial `process.wait()` as the whole launcher lifetime. Its bounded owner loop tracks the current owned backend across an intentional Restore stop/restart and never terminates a newly restarted backend through a stale reference to the original child.

No process is discovered/killed by port, PID lookup, name or command pattern. Only `BackendProcessOwner` may stop/start the launcher-owned child.

### Restart handoff after C4-I

After `execute_restore(...)` returns:

#### If `normal_startup_allowed` is true

The main launcher runtime attempts to restore ordinary product service against the canonical `context.database_path`:

```text
C4-I returns with maintenance lease held and no ordinary backend
→ require/retain maintenance exclusion
→ release maintenance lease immediately before exact owned backend start
→ context.backend.start(config, paths, context.database_path)
→ child proves canonical liveness lock + listening socket
→ only then publish restore_completed / restore_failed
```

No extra migration/startup algorithm is invented in B2. A pre-replacement refusal uses the already-started/migrated original database; completed/rollback C4-I paths already ran the existing startup/migration rules they require.

If ordinary backend restart fails after a safe C4-I result:

- do not reinterpret the Restore outcome;
- do not roll back merely because restart failed;
- reacquire/retain the maintenance lease when no backend owns it;
- publish `restore_blocked` with fixed non-technical restart guidance;
- leave the durable C4-I record and data exactly as C4-I left them.

If maintenance exclusion itself cannot be safely re-established, B2 fails closed and does not claim ordinary operation.

#### If `normal_startup_allowed` is false

Do not start the ordinary backend. Keep/restore maintenance exclusion and publish `restore_blocked` with the C4-I safe message/failure category.

#### Retryable verification environment

If C4-I raises its existing retryable backend-start/port condition, B2 does not convert it into a Restore failure and does not start ordinary service over an unresolved durable phase. It publishes `restore_blocked` using the existing safe retry guidance; the next launcher start resumes through the accepted startup-recovery matrix.

### Result handoff

The main launcher runtime is the only publisher of the destructive result back into the control session.

Publication is matched to the exact accepted execution intent. A stale selection worker, later command or expired browser token may not overwrite the launcher-owned result.

The result is in-memory for the current launcher run only. B2 adds no new persistence. Durable truth remains the C4-I operation record; C4-II-C later owns full user-facing completion/rollback/restart/support presentation.

### B2 allowed implementation surface

The implemented surface is limited to what is required for this coordinator/control seam:

```text
launcher/restore/control_protocol.py
launcher/restore/control_session.py
launcher/restore/control_plane.py
launcher/runtime.py
launcher/restore/execution_coordinator.py
launcher/tests/test_restore_execution_coordinator.py
docs/state lifecycle/checker files
```

No `BackendProcessOwner` ownership/stopping semantics are changed.

The following closed B1/C4-I implementations remain byte-identical:

```text
launcher/restore/contracts.py
launcher/restore/engine.py
launcher/restore/source_proof.py
launcher/restore/staging.py
launcher/restore/validation_session.py
launcher/restore/validation_scratch.py
launcher/restore/context.py
launcher/restore/verification.py
```

A3 picker, A4 browser handoff and all frontend source also remain byte-identical. Ordinary FastAPI backend, migrations, dependencies and packaging resources are outside B2.

### B2 hard prohibitions

B2 must not:

- add browser confirmation/button/UI;
- modify current frontend contracts or presentation;
- add `/v1/restore/confirm`;
- accept a source path/proof/digest from browser;
- execute C4-I from an HTTP request thread or selection worker;
- create a second destructive engine or duplicate staging/validation/safety-copy/replacement/rollback logic;
- add a cancel-destructive-Restore command;
- let heartbeat/session expiry abort destructive C4-I;
- expose operation ID, durable record, internal path or technical exception text;
- persist A1 proof/path/session token/intent/result;
- change the twelve durable phases, recovery matrix or Restore AuditLog semantics;
- add a new dependency, service, port or helper executable;
- authorize B3/C4-II-C/C4-III.

### Required B2 tests

The current changeset includes focused tests intended to prove the B2 seams below. They are **not considered PASS until run against the published exact head**.

At minimum prove:

- `/v1/restore/execute` exact schema accepts only `request_id`, `command_seq`, `generation`;
- no path/proof/digest can cross HTTP;
- wrong Host/Origin/auth/schema cannot consume sequence;
- exact-next sequence is consumed before business preconditions;
- same request ID/sequence retry queues and executes at most once;
- same sequence/different request conflicts; stale/future sequence is refused;
- stale/non-accepted generation queues nothing;
- missing retained A1 proof queues nothing;
- control generation and retained-proof generation need not be numerically equal;
- accepted execution atomically invalidates retained source authority;
- queued intent carries launcher-private path + B1 expected proof only in memory;
- HTTP/session worker never calls `execute_restore(...)`;
- main runtime consumes the intent and calls existing C4-I exactly once;
- `ProofBoundRestoreRequest` is constructed from retained A1 proof, never browser values;
- control plane remains reachable on the same port while ordinary backend is stopped;
- heartbeat/state remain responsive during `restoring`;
- select/cancel/second execute during `restoring` cannot cancel or duplicate destructive work;
- session expiry during `restoring` invalidates browser auth but does not cancel C4-I or overwrite final launcher-owned state;
- completed C4-I + successful backend restart publishes `restore_completed`;
- safe failed/rolled-back C4-I + successful restart publishes `restore_failed`;
- source-changed/pre-replacement refusal restarts ordinary backend and leaves working DB unchanged;
- `normal_startup_allowed=false` publishes `restore_blocked` and starts no ordinary backend;
- retryable verification-port condition publishes `restore_blocked` without changing durable phase;
- backend restart failure does not rewrite/rollback C4-I result and leaves maintenance exclusion safe;
- intentional C4-I stop of the original backend does not terminate the launcher runtime or kill a newly restarted child;
- existing A1/A2/A3/A4/B1/C4-I regressions remain green;
- frontend source remains byte-identical in B2;
- external exact-head smoke proves one authenticated execute intent, real backend stop, B1 re-proof, C4-I execution and safe restart/result handoff using isolated data/processes.

## B3 — Browser explicit destructive confirmation — PLANNED — NOT AUTHORIZED

B3 remains blocked until B2 is merged, exact-head verified and separately lifecycle-closed.

Future B3 will extend the browser TypeScript contract for the B2 execution states and add the explicit human confirmation UI that sends `/v1/restore/execute` only after the user confirms. Browser filename/state/token/generation remain presentation/reference values, never source proof.

B2's existence is not permission to surface a destructive button early.

## Successor discipline

Each B slice is a separate PR with exact changed-path review, tests, smoke and independent P0/P1/P2 audit. B2 implementation in the current changeset does not imply closure. B2 merge does not authorize B3. A separate lifecycle closure is required, and C4-II-C/C4-III remain separately blocked.
