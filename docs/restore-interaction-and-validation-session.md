# Restore interaction and non-destructive validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-07`

Normative sources:

- `docs/decisions/0016-launcher-assisted-restore.md` — durable Restore safety and
  twelve-phase state machine;
- `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md` — C4-I
  lifecycle closure and CR-011 authorization;
- `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md` —
  selected CR-011 interaction architecture;
- `docs/current-lifecycle.md` — current authorization and sequencing.

ADR 0018 does not amend ADR 0016 safety semantics.

## Current lifecycle

```text
PR #171 — MERGED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — DECIDED — ADR 0018 ACCEPTED — NORMATIVE ON MAIN
C4-II-A — PLANNED — NOT AUTHORIZED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

On a CR-011 PR branch the decision is a changeset proposal; it becomes normative
only when present on `main`. C4-II-A is not authorized by this profile.

## Selected interaction architecture

CR-011 selects a **narrowly authenticated launcher-owned loopback control
plane**.

```text
ordinary browser / SPA
  ├── business API ──→ ordinary FastAPI backend
  └── Restore control ──→ launcher control plane
                           127.0.0.1:<ephemeral>
                                  ↓
                           launcher-owned picker
                                  ↓
                      launcher validation session
                                  ↓
                    C4-I intake/staging/validation
```

The control plane is not an ordinary backend route and is not a generic local
command server.

No WebSocket is selected. No new application dependency is authorized.

## Browser bootstrap contract

Future C4-II-A must implement these properties:

1. launcher binds control plane to exactly `127.0.0.1` on an OS-assigned
   ephemeral port;
2. launcher creates one opaque run ID and a one-use random bootstrap token with
   at least 256 bits of entropy;
3. launcher opens the browser with the control port + bootstrap token in the URL
   **fragment**, never query parameters;
4. the frontend exchanges that capability with `POST /v1/bootstrap`;
5. the control plane accepts only the exact configured local frontend Origin;
6. bootstrap token is invalidated after the first successful exchange;
7. frontend removes the bootstrap fragment immediately;
8. control plane returns a second random run-scoped session token;
9. frontend stores that session token only in `sessionStorage`, never
   `localStorage`;
10. session token is sent only in an explicit authorization header;
11. all tokens are invalidated on launcher exit/restart and are never persisted or
    logged.

CORS must use one exact origin. Wildcard CORS and credentialed cookie sessions are
forbidden.

For user mode, the frontend origin must be local HTTP on `127.0.0.1` with the
configured frontend port. A different origin is refused instead of being added
dynamically.

## Browser liveness

While a Restore control session is active:

- browser heartbeat interval: 15 seconds;
- session expires after 60 seconds without an authenticated heartbeat or other
  authenticated control request.

Expiry must:

- invalidate the run-scoped browser token;
- invalidate the active selection generation;
- prevent stale result publication;
- terminate an owned picker child when needed;
- clean only owned validation scratch;
- leave ordinary backend/workshop data unchanged.

A browser reload may recover through `sessionStorage` + `GET /v1/state`.
Closing the browser/tab must never authorize any destructive action.

## Narrow control vocabulary

C4-II-A may expose only an equivalent of:

```text
POST /v1/bootstrap
GET  /v1/state
POST /v1/heartbeat
POST /v1/restore/select
POST /v1/restore/cancel
```

No destructive execute/confirm endpoint belongs in C4-II-A.

No arbitrary filesystem, shell, SQL, proxy or generic launcher command endpoint
is allowed.

## Request replay and duplicate protection

Every authenticated non-read command carries a cryptographically strong request
ID.

The launcher keeps a bounded per-run replay/idempotency ledger:

- same request ID never performs the action twice;
- duplicate completed request yields the same safe result/reference;
- duplicate in-progress request does not create second ownership;
- a new `select` while another picker/validation action owns the session is
  rejected as action-in-progress;
- accepted select/cancel/reselect increments a monotonically increasing selection
  generation;
- a result may publish only if its captured generation is still current;
- cancellation/reselection invalidates older generations before cleanup.

## Native macOS picker

The launcher owns picker authority.

Future adapter:

```text
launcher
→ owned short-lived /usr/bin/osascript child
→ macOS Standard Additions `choose file`
→ POSIX selected path returned only to launcher
```

Requirements:

- no `shell=True`;
- no user-controlled text interpolated into executable AppleScript;
- no `System Events` automation of another application;
- cancellation is a typed ordinary cancel result;
- no absolute path is returned to browser or ordinary backend;
- filename/type filters are presentation hints only and never acceptance proof.

CR-011 authorizes no PyObjC, Electron, Tauri, pywebview, tkinter or other new
runtime dependency.

Mac App Store sandbox compatibility is not claimed. A future sandboxed packaging
decision may replace the picker adapter while preserving launcher ownership and
path privacy.

## Mandatory non-destructive application boundary

Future C4-II-A must implement one launcher-owned service conceptually equivalent
to:

```text
prepare_restore_candidate(...)
```

It must:

- never call `execute_restore(...)`;
- create no durable Restore operation record;
- enter none of the twelve durable Restore phases;
- create no `before_restore` safety copy;
- replace no working database;
- migrate no working database;
- perform no rollback/startup-recovery mutation;
- write no Restore AuditLog event;
- leave the original selected source byte-identical;
- use isolated temporary validation scratch outside durable Restore operation
  workspaces;
- reuse accepted C4-I source intake, sidecar checks, held-descriptor identity,
  full digest stability proof, staging and candidate validation;
- return typed presentation-safe results only;
- keep raw SQLite errors, stack traces, migration IDs and internal paths in local
  technical logs only;
- expose opaque run/session/generation identities only;
- clean owned scratch on cancel/reselect/rejection/failure/shutdown;
- provide bounded next-run cleanup after interruption;
- never claim Restore completed.

If `stage_source(...)` is too coupled to `RestoreWorkspace`, C4-II-A may make a
bounded shared-primitive refactor, but must preserve the existing C4-I algorithm
and tests. A second weaker staging/validation implementation is forbidden.

## Validation scratch

Use a canonical launcher-owned root under the current user's system temp area,
conceptually:

```text
<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/
```

Rules:

- no user-provided path component;
- opaque random run/session identifiers;
- no symlink traversal;
- ownership/version marker sufficient to prove cleanup ownership;
- cleanup refuses paths outside the canonical root;
- scratch never appears as a durable Restore operation;
- next-run cleanup removes only recognized owned session directories.

## Typed browser-visible result

Allowed presentation facts include:

- opaque run/session identity;
- selection generation;
- safe display filename/label;
- state: idle/selecting/validating/accepted/rejected/cancelled/technical failure;
- current-schema or older-supported-schema compatibility;
- fixed rejection category;
- fixed human guidance;
- stale/cancelled flag.

Forbidden browser-visible data:

- absolute source path;
- staged candidate path;
- raw SQLite/SQL text;
- migration IDs;
- operation-record contents;
- stack traces;
- arbitrary database contents.

A displayed filename is not compatibility proof.

## Retained launcher-private proof

After successful validation, delete the temporary staged candidate.

For the current launcher run, retain in launcher memory only:

- canonical absolute source path;
- C4-I `SourceIdentity` facts;
- full SHA-256 digest from the held descriptor;
- successful selection generation;
- typed compatibility result.

The browser session token references this state but is not authority.

Future C4-II-B must, before destructive execution:

```text
reopen original launcher-private path through C4-I intake
→ compare descriptor/path identity
→ recompute and compare full SHA-256
→ re-check sidecars/self-containment
→ stage again through C4-I semantics
→ validate again
→ only then enter existing C4-I destructive execution boundary
```

Any mismatch invalidates the prior validation and returns to source selection.
Filename, extension, browser state or token possession cannot bypass re-proof.

## Backend lifecycle

The ordinary backend remains running during:

- native file selection;
- source intake;
- temporary staging;
- candidate validation;
- validation-result presentation.

This is intentional because C4-II-A is non-destructive and works only on the
selected source + isolated staged copy. It must not acquire destructive authority
merely because validation is occurring.

Future C4-II-B remains responsible for the existing C4-I backend stop/exclusion
proof before destructive replacement.

## Cleanup matrix

| Event | Required behavior |
|---|---|
| Picker cancel | advance/invalidate generation, no durable operation, clean owned scratch |
| Reselect | invalidate old generation first, clean old ownership, then start new generation |
| Validation rejection | keep safe rejection category only, clean staged scratch |
| Technical failure | technical detail local only, safe browser message, clean owned scratch |
| Browser reload | recover typed state through current run-scoped session |
| Browser/tab close | heartbeat timeout invalidates control authority and cleans active validation ownership |
| Launcher normal exit | invalidate tokens, cancel active generation, stop picker helper/control plane, clean scratch |
| Launcher crash/machine interruption | no token survives; next run performs bounded recognized-scratch cleanup only |

Validation scratch must never trigger a Restore phase, startup recovery or working
database mutation.

## Future C4-II-A minimum automated tests

At minimum prove:

1. loopback-only ephemeral binding;
2. exact Origin enforcement and no wildcard CORS;
3. one-use bootstrap capability;
4. old-run/wrong session token rejection;
5. replay/idempotency behavior;
6. duplicate select rejection;
7. stale generation cannot publish;
8. browser payload contains no absolute path;
9. picker cancellation is typed and non-destructive;
10. valid current and supported older backup acceptance;
11. newer/foreign/empty/corrupt/directory/symlink/path-escape rejection;
12. original selected source remains byte-identical;
13. no durable Restore operation, phase, safety copy or AuditLog event;
14. no working database replacement/migration;
15. backend remains usable during validation;
16. cleanup removes only proved owned scratch;
17. browser reload recovers safe state;
18. heartbeat expiry invalidates stale control authority.

## Future exact-head macOS smoke

Smoke must use the real selected architecture:

```text
real launcher run
→ real browser Restore screen
→ real authenticated launcher-control request
→ real /usr/bin/osascript native picker
→ select prepared temporary workshop backup
→ real candidate preparation/validation
→ typed browser result
→ cancel/reselect exercise
→ prove source bytes unchanged
→ prove no durable Restore operation/safety copy/working-DB change
→ prove owned processes/control plane/scratch cleaned
```

Injecting the final validation result or bypassing the picker/control/session
boundary is not sufficient.

## Not authorized yet

This profile does not authorize:

- C4-II-A runtime implementation;
- C4-II-B/C4-II-C/C4-III;
- frontend Restore controls;
- launcher control-plane code;
- picker code;
- validation-session code;
- destructive Restore confirmation/execution;
- new dependencies;
- packaging implementation;
- changes to ADR 0016 state-machine/recovery semantics.

A separate post-CR-011 task must explicitly authorize bounded C4-II-A runtime
work.