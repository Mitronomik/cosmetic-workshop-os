# cosmetic-workshop-os — Active implementation plan

Project: `cosmetic-workshop-os`
Client-facing name: **Мастерская косметолога**
Status: **active current implementation sequence**
Updated: `2026-08-07`

The complete pre-compaction plan remains byte-for-byte preserved at:

`docs/history/implementation-plan/2026-08-06-pre-compaction.md`

Searchable C4-I implementation/audit history remains at:

`docs/history/c4-i-implementation-and-audit-history.md`

Historical files are evidence, not current authorization.

## 1. Source of truth

Read current work in this order:

1. applicable `AGENTS.md` files;
2. newest accepted ADR for the exact topic;
3. `docs/current-lifecycle.md`;
4. durable older ADRs for unsuperseded safety/product semantics;
5. `docs/restore-interaction-and-validation-session.md`;
6. `docs/c4-ii-a-implementation-slices.md` for current C4-II-A slicing;
7. this plan;
8. active `state/` files;
9. strategic/large references;
10. `docs/history/`.

Restore authority is split deliberately:

- ADR 0016 — durable destructive Restore safety/state machine;
- ADR 0017 — C4-I lifecycle closure and CR-011 gate history;
- ADR 0018 — accepted interaction/control/picker/validation-session architecture;
- `docs/c4-ii-a-implementation-slices.md` — bounded implementation authorization;
- `docs/current-lifecycle.md` — current runtime authorization and sequencing.

## 2. Current merged baseline

PR #170 / C4-I:

- reviewed head: `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8`;
- merge commit: `e6997281d2e0268ce54184d988c114bac71c35e2`;
- C4-I: `DONE — MERGED AND EXACT-HEAD VERIFIED`.

PR #171 / project-memory closure:

- reviewed head: `4978aa9a7c05117011eae1bc00276d5f98378d9b`;
- merge commit: `76ab59216047222714a32f2793a789b3dc8df19a`.

PR #172 / CR-011 interaction decision:

- reviewed head: `c51d5baa07e4cd8912b1973649c22b20f581e3d2`;
- merge commit: `998596560db6780a677bdec363d1fd19db30c1b6`;
- merged at: `2026-08-07T12:57:28Z`;
- final architecture audit: P0=0, P1=0, P2=0;
- real checkout documentation gate: PASS.

## 3. Current lifecycle

```text
PR #171 — MERGED
PR #172 — MERGED — CR-011 ACCEPTED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — AUTHORIZED AS SLICED — NOT IMPLEMENTED
C4-II-A1 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A2 — PLANNED — BLOCKED BY A1 MERGE + EXACT-HEAD GATE
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
installation verification — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

On PR #173, this authorization is a documentation/lifecycle changeset and becomes
normative only after merge to `main`. No A1 runtime work belongs in PR #173.

## 4. Accepted CR-011 architecture

ADR 0018 selects:

```text
ordinary browser presentation
→ exact-run authenticated launcher-owned HTTP control plane
  on 127.0.0.1:<ephemeral>
→ launcher-owned macOS picker via owned /usr/bin/osascript child
→ launcher-owned non-destructive validation session
→ existing C4-I intake/staging/validation semantics
```

Durable commitments include exact Origin/Host/run binding, no wildcard CORS,
one-use bootstrap, run-scoped browser session, path privacy, responsive
cancel/liveness, non-replayable command ordering, worker-quiescence cleanup,
ordinary backend availability during C4-II-A validation and mandatory C4-II-B
source re-proof before destructive execution.

Complete architecture contract:

- `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`;
- `docs/restore-interaction-and-validation-session.md`.

## 5. Current implementation window — PR #173 authorization/slicing

PR #173 is **documentation/lifecycle only**.

Allowed:

- record PR #172 as merged / CR-011 accepted;
- authorize C4-II-A only as A1→A4 bounded slices;
- authorize A1 as the only immediate runtime successor;
- define A2/A3/A4 predecessor gates;
- preserve C4-II-B as not authorized;
- synchronize README/current lifecycle/state/Restore status surfaces;
- update the strict documentation lifecycle checker.

Forbidden:

- backend/frontend/launcher runtime or test changes;
- A1 implementation;
- control-plane/picker/frontend Restore code;
- dependency/lockfile changes;
- migrations;
- packaging implementation;
- destructive Restore changes.

Required PR #173 checks:

```text
git diff --check
python3 scripts/check_documentation_lifecycle.py
repository-defined docs/link checker if present
verify docs/state/checker-only diff
fresh independent exact-head authorization audit
P0=0, P1=0, P2=0
```

Product smoke is not applicable to PR #173 because runtime behavior is unchanged.

## 6. C4-II-A implementation slices

Normative implementation plan:

`docs/c4-ii-a-implementation-slices.md`.

### A1 — Validation-session core — AUTHORIZED NEXT

Implement only:

- launcher-owned `prepare_restore_candidate(...)`-equivalent;
- isolated validation scratch;
- shared-safe reuse/refactor of C4-I intake/staging/validation;
- typed validation result;
- generation/stale/cancel/invalidation semantics;
- launcher-private source path + `SourceIdentity` + SHA-256 retained proof;
- owned-only cleanup and interruption cleanup;
- automated tests and service-level exact-head smoke.

Do not implement HTTP control plane, browser token/bootstrap, native picker,
frontend Restore UI or any destructive Restore authority in A1.

### A2 — Exact-run launcher control plane — BLOCKED BY A1 MERGE

After A1 merge/exact-head gate, implement the loopback control/session protocol:
Host/Origin, bootstrap, run token, heartbeat/expiry, concurrency, `command_seq`,
idempotent retry, cancellation and typed state. No real picker or final UI.

### A3 — Native macOS picker integration — BLOCKED BY A2 MERGE

After A2 merge/exact-head gate, integrate owned `/usr/bin/osascript` + Standard
Additions `choose file`, picker worker lifecycle, cancellation/expiry and A1
candidate preparation. No final browser Restore workspace.

### A4 — Browser Restore screen — BLOCKED BY A3 MERGE

After A3 merge/exact-head gate, deliver `/backups/restore`, entry from `/backups`,
fragment bootstrap handling, `sessionStorage` control metadata, typed safe states,
select/cancel/reselect/reload UX and real end-to-end non-destructive macOS smoke.

Each slice is a separate PR from updated `main`. Do not branch a later slice from
an unmerged predecessor.

## 7. Mandatory C4-II-A non-destructive boundary

No A1–A4 slice may:

- call `execute_restore(...)`;
- create a durable Restore operation;
- enter any of the twelve durable phases;
- create `before_restore` safety copy;
- replace/migrate working database;
- perform rollback/startup-recovery mutation;
- write Restore AuditLog;
- expose authoritative absolute source path to browser/backend;
- infer compatibility from filename/extension;
- create a second weaker staging/validation algorithm.

C4-I source-intake, held-descriptor, sidecar, two-pass digest staging and candidate
validation semantics remain the source of truth.

## 8. C4-II-B handoff remains blocked

C4-II-B remains separately `PLANNED — NOT AUTHORIZED`.

Before destructive execution it must eventually:

```text
reopen launcher-private original path
→ compare C4-I SourceIdentity
→ recompute full SHA-256
→ re-check sidecars/self-containment
→ stage again
→ validate again
→ prove backend exclusion
→ create mandatory before_restore safety copy
→ only then enter C4-I destructive execution
```

No C4-II-A browser/session token is destructive authority.

## 9. Open product obligations

- merge PR #173 authorization/slicing;
- implement/review/merge A1;
- then A2;
- then A3;
- then A4 + exact-head non-destructive end-to-end smoke;
- separately authorize C4-II-B;
- implement C4-II-B destructive confirmation/execution;
- C4-II-C outcome/restart/support UX;
- C4-III end-to-end Restore lifecycle closure;
- macOS `.app`/`.dmg` packaging;
- safe packaged update flow;
- installation verification;
- full release-candidate smoke.

Do not collapse these into one broad PR.

## 10. Current next action

```text
Finish, validate and independently audit PR #173.
Do not implement A1 on the unmerged authorization branch.
After PR #173 merges, create a fresh branch from updated main and implement only C4-II-A1.
```
