# C4-II-B implementation authorization and slice plan

Status: **NORMATIVE IMPLEMENTATION PLAN**
Updated: `2026-08-11`

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
PR #184 reviewed B2 head — 1ae8bfcdf0f1f1798ce85eac0931925d029379c4
PR #184 / B2 merge — 266c50a77e5f353fa77701cb854629a99460667f
PR #185 reviewed B3-authorization head — f206cf4896abcc7e8ecd0266cacd3f8a6d89e22c
PR #185 / B3-authorization merge — f6589bdd7c403b6d400e3f5b7a0daea75b14632a
```

## Current slice status

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

B2 is lifecycle-closed on merged PR #184. PR #185 authorized B3 only. B3 code exists in the current changeset but is not closed until exact-head build/tests/UI smoke/audit, merge and a separate lifecycle closure are complete.

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

## B2 — Launcher destructive coordinator/control command — DONE — MERGED AND EXACT-HEAD VERIFIED

### Goal

Add one bounded launcher-owned bridge from the existing exact-run control session into the existing C4-I engine without moving destructive work into HTTP threads, browser code or a second Restore implementation.

The closed B2 architecture is:

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

### Accepted B2 closure evidence

- reviewed exact head `1ae8bfcdf0f1f1798ce85eac0931925d029379c4`;
- merge/new main `266c50a77e5f353fa77701cb854629a99460667f`;
- focused B2/runtime tests: **37 PASS** in the independent audit;
- launcher regression: **636 PASS**;
- backend regression: **1867 PASS**;
- full backend + launcher: **2503/2503 PASS**;
- frontend Restore regression: **16/16 PASS**;
- anti-hang owner-loop gate: **PASS**, autonomous, no manual `Ctrl+C`;
- corrected external exact-head isolated process smoke: **PASS**;
- external smoke proved production A4 handoff before bootstrap, authenticated `select → accepted → execute`, `restore_accepted / restoring`, same control-plane port through ordinary-backend stop and real C4-I verification lifetimes, durable phase `completed`, safe ordinary-backend restart, `restore_completed`, and isolated cleanup;
- independent audit: **P0=0 / P1=0 / P2=0 — AUDIT GATE PASS**;
- final no-change exact-head / clean-worktree gate: **PASS**.

The earlier eight-hour run that required repeated manual `Ctrl+C` remains **INVALID / NOT A PASS**. The first external smoke runner remains **INCONCLUSIVE RUNNER** because it consumed the one-use bootstrap before the production A4 handoff; it is neither product PASS nor product failure evidence.

The lifecycle checker pins the accepted merged B2 production blobs as a closed boundary.

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

They are launcher/control protocol states only. Existing A4 frontend code remained byte-identical in B2 and therefore did not initiate or present B2 execution.

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

### Closed B2 implementation surface

The accepted merged surface is:

```text
launcher/restore/control_protocol.py
launcher/restore/control_session.py
launcher/restore/control_plane.py
launcher/runtime.py
launcher/restore/execution_coordinator.py
```

No `BackendProcessOwner` ownership/stopping semantics changed.

The following B1/C4-I implementations remain byte-identical:

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

A3 picker and A4 browser handoff remain protected by the B3 implementation gate.

### B2 hard prohibitions — closed evidence

The merged B2 implementation did not:

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
- add a new dependency, service, port or helper executable.

### Accepted B2 tests

The following classes of tests are accepted on the reviewed head:

- exact `/v1/restore/execute` schema and privacy;
- Host/Origin/auth/schema before sequence consumption;
- exact-next replay/one-shot semantics;
- stale/non-accepted generation and missing proof refusals;
- distinct control/proof generation domains;
- immediate retained-authority invalidation;
- HTTP/session never calling C4-I;
- main runtime consuming intent exactly once;
- control plane surviving ordinary backend stop;
- restoring-time heartbeat/state and duplicate command refusal;
- session expiry non-cancellation;
- completed/failed/blocked result mappings;
- SOURCE_CHANGED pre-replacement refusal with unchanged working DB;
- restart failure and retryable-port fail-closed behavior;
- backend-exit race sealing;
- existing A1/A2/A3/A4/B1/C4-I regressions;
- external isolated process smoke.

## B3 — Browser explicit destructive confirmation — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED

### Goal

Connect the accepted A4 browser Restore route to merged B2 only after explicit human confirmation.

```text
A4 browser Restore route
→ candidate state = accepted
→ explicit destructive confirmation
→ dismiss locally OR confirm
→ frontend creates one pending execute command
→ authenticated POST /v1/restore/execute
   exact request_id + command_seq + generation
→ B2 authority-transfer boundary
→ browser follows pathless launcher state
```

B3 is frontend-only except focused frontend tests and lifecycle/checker/status docs. **No launcher/backend changes are authorized or implemented**.

### Implementation status in this changeset

The current B3 production surface is exactly:

```text
frontend/src/restore-control-contract.ts
frontend/src/restore-control-runtime.ts
frontend/src/restore-control-presentation.ts
frontend/src/restore-control-entry.ts
```

Focused tests are:

```text
frontend/test/restore-control.test.mjs
frontend/test/restore-control-races.test.mjs
```

`frontend/src/main.ts` and `frontend/src/app-navigation-routes.ts` remain byte-identical to the PR #185 merge baseline. No launcher/backend/migration/dependency/package-resource implementation is changed.

No test result is implied by implementation presence. Exact-head verification remains a separate merge gate.

### Browser authority boundary

The browser may use the safe display filename and accepted control `generation`. It never knows, sends or persists absolute source path, source identity, SHA-256, `ExpectedSourceProof`, working database path, backup directory, Restore workspace, safety-copy path, operation ID, durable operation record, lock path, SQL or traceback.

Filename is display-only. `generation` is a stale-view guard, never source proof.

### Frontend control states

B3 adds exactly these existing launcher states to TypeScript parsing:

```text
restoring
restore_completed
restore_failed
restore_blocked
```

Unknown states continue to fail closed. The launcher snapshot shape is unchanged.

### Execute command and generation ownership

B3 adds frontend action `execute`, calling only `POST /v1/restore/execute` with exact `request_id + command_seq + generation`. No additional request key is emitted. `/v1/restore/confirm` remains forbidden: confirmation is browser presentation, not a second authority endpoint.

The DOM confirmation layer does not provide generation. `RestoreControlRuntime.execute()` reads the current parsed snapshot and proceeds only when state is `accepted` with a valid positive generation. This prevents a stale or arbitrary DOM value from selecting destructive authority.

### Replay requirement — load-bearing

Replay format remains version `1` for backward compatibility.

Pending commands are discriminated:

```text
select/cancel:
  action
  requestId
  commandSeq

execute:
  action
  requestId
  commandSeq
  generation
```

The historical select/cancel shape remains valid unchanged. Execute requires the accepted positive generation and exact keys.

If the execute transport result is ambiguous, retry sends the **same request ID, same command sequence and same generation**. It does not allocate a new request ID or sequence. No filesystem authority is stored in history/session replay state.

The pending execute is persisted before network I/O. A second near-simultaneous execute therefore sees an existing pending command and sends no second destructive request.

### Confirmation UX

Confirmation is shown only for the current `accepted` candidate while the exact-run session is ready, protocol-safe and has no pending command.

The native semantic `<dialog>`:

- identifies the backup via safe escaped display filename;
- explains that current workshop data will be replaced;
- explains temporary application unavailability;
- explains that existing Restore safety logic creates a protective copy before replacement;
- explains that an already started Restore cannot be cancelled from this screen;
- focuses the safe `Вернуться` action first;
- keeps `Восстановить данные` as the explicit danger action.

Dismissing the dialog or pressing Escape is local-only and does not implicitly call `/v1/restore/cancel` or execute.

The local confirmation is bound to the current accepted generation. Any runtime view/generation/pending change invalidates it.

### Restoring and minimal final presentation

While `restoring`, B3 shows a clear non-technical in-progress state, disables duplicate confirmation, offers no select/cancel/destructive cancellation, displays no fake progress/phase, and continues launcher-control polling.

For `restore_completed`, `restore_failed`, `restore_blocked`, B3 minimally displays the safe launcher message. It does not infer durable phase or implement the richer completion/rollback/restart/support experience owned by C4-II-C.

Generic post-execute network guidance does not claim working data was unchanged because destructive work may already have started.

### Required B3 tests in this changeset

The focused suite is designed to prove:

- existing A4 states still parse;
- exactly four B2 execution states parse and unknown state fails closed;
- snapshot exact-key validation still rejects path extras;
- select/cancel replay remains backward-safe;
- execute replay requires exact generation and rejects filesystem-authority extras;
- execute request body contains exactly request ID, command sequence and generation;
- generation comes from current `accepted` snapshot;
- execute from non-accepted state sends nothing;
- ambiguous execute retry preserves exact ID/sequence/generation and does not allocate another sequence;
- reload preserves a pending execute safely;
- two concurrent execute calls emit exactly one destructive request;
- accepted presentation requires explicit confirmation;
- dialog copy explains replacement/protective copy and safe action owns initial focus;
- restoring presentation has no select/cancel/reconfirm/fake percentage;
- final B2 states minimally render safe launcher messages;
- entry handles Escape/dismiss locally rather than as Restore cancel;
- no localStorage/browser file-input/path authority appears in Restore frontend source.

### Verification still required before merge

The published B3 exact head must still run and record:

- `git diff --check`;
- lifecycle checker;
- frontend build/type-check;
- focused `test:restore-control` suite;
- existing A4 regressions;
- desktop `/backups/restore` smoke;
- narrow-screen Restore smoke;
- keyboard focus/Escape dialog smoke;
- loading/network/restoring/final/disabled-state review;
- clean exact head/worktree;
- independent `P0=0 / P1=0 / P2=0` audit.

Do not record these as PASS until actually observed on the published PR head.

## Successor discipline

Each B slice is a separate PR with exact changed-path review, tests, appropriate smoke and independent P0/P1/P2 audit. B3 implementation does not authorize C4-II-C or C4-III. After B3 merges, a separate lifecycle closure is required before any C4-II-C authorization. Product Restore remains NOT IMPLEMENTED.