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
6. this plan;
7. active `state/` files;
8. strategic/large references;
9. `docs/history/`.

Restore authority is split deliberately:

- ADR 0016 — durable destructive Restore safety/state machine;
- ADR 0017 — C4-I lifecycle closure and CR-011 gate;
- ADR 0018 — selected CR-011 interaction and validation-session architecture.

## 2. Current merged baseline

PR #170 / C4-I:

- reviewed head: `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8`;
- merge commit: `e6997281d2e0268ce54184d988c114bac71c35e2`;
- C4-I: `DONE — MERGED AND EXACT-HEAD VERIFIED`.

PR #171 / project-memory and CR-011 gate:

- reviewed head: `4978aa9a7c05117011eae1bc00276d5f98378d9b`;
- merge commit: `76ab59216047222714a32f2793a789b3dc8df19a`;
- merged: `2026-08-07T11:23:42Z`.

PR #171 changed documentation/state plus the documentation lifecycle checker only.

## 3. Current lifecycle

```text
PR #171 — MERGED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — DECIDED — ADR 0018 ACCEPTED — NORMATIVE ON MAIN
C4-II-A — PLANNED — NOT AUTHORIZED
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

On the CR-011 PR branch, ADR 0018 becomes project authority only after merge to
`main`. No successor runtime work belongs on the decision branch.

## 4. CR-011 selected architecture

ADR 0018 selects:

```text
ordinary browser presentation
→ exact-run authenticated launcher-owned HTTP control plane
  on 127.0.0.1:<ephemeral>
→ launcher-owned macOS picker via owned /usr/bin/osascript child
→ launcher-owned non-destructive validation session
→ existing C4-I intake/staging/validation semantics
```

Security/product commitments:

- control plane is separate from ordinary FastAPI business API;
- no WebSocket and no generic localhost command server;
- no new application dependency;
- exact configured local frontend Origin only; no wildcard CORS;
- one-use 256-bit bootstrap capability delivered in URL fragment;
- fragment removed after bootstrap;
- second 256-bit run-scoped session token stored in browser `sessionStorage`
  only;
- session heartbeat 15s, expiry after 60s without authenticated activity;
- replay/idempotency request IDs and monotonically increasing selection
  generation;
- absolute selected-source path stays launcher-private;
- browser sees typed safe result only;
- ordinary backend remains running during non-destructive validation;
- picker uses `/usr/bin/osascript` + Standard Additions `choose file`, no
  `shell=True`, no `System Events`;
- validation scratch is temporary and never a durable Restore operation;
- successful C4-II-A validation deletes staged scratch and retains launcher-memory
  source identity + SHA-256 proof only;
- future C4-II-B must reopen, re-prove, restage and revalidate before destructive
  execution.

Complete contract:

- `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`;
- `docs/restore-interaction-and-validation-session.md`.

## 5. Current implementation window — CR-011 decision PR

This changeset is **documentation/architecture only**.

Allowed:

- ADR 0018;
- lifecycle/project-memory synchronization;
- Restore interaction profile;
- deployment/packaging documentation consequences;
- strict documentation lifecycle checker updates.

Forbidden:

- backend production/test code;
- frontend production/test code;
- launcher production/test code;
- native picker implementation;
- control-plane implementation;
- validation-session implementation;
- dependencies/lockfiles;
- migrations;
- packaging implementation;
- destructive Restore changes.

Before merge:

```text
git diff --check
python3 scripts/check_documentation_lifecycle.py
repository-defined docs/link checker if present
verify no backend/frontend/launcher runtime path changed
fresh independent exact-head architecture audit
resolve all P0/P1/P2 findings
```

Product smoke is not applicable to this decision-only PR.

## 6. C4-II-A remains not authorized

ADR 0018 removes the architectural ambiguity but does **not** authorize runtime
implementation.

After the CR-011 decision merges, create a separate bounded authorization/task
for C4-II-A.

That future task may authorize only:

- exact-run launcher control-plane bootstrap/session boundary;
- dedicated browser Restore source-selection/validation presentation;
- launcher-owned `/usr/bin/osascript` picker adapter;
- launcher-owned non-destructive `prepare_restore_candidate(...)`-equivalent;
- shared-safe refactor required to reuse C4-I staging/validation primitives;
- typed safe result state;
- cancellation/reselection/replay/stale-generation protection;
- validation scratch cleanup;
- automated tests and exact-head real-boundary macOS smoke.

It must not authorize C4-II-B destructive execution.

## 7. Mandatory future validation contract

Future C4-II-A must not:

- call `execute_restore(...)`;
- create a durable Restore operation;
- enter any of the twelve durable phases;
- create `before_restore` safety copy;
- replace/migrate working database;
- perform rollback/startup-recovery mutation;
- write a Restore AuditLog event;
- expose authoritative absolute source path to browser/backend;
- infer compatibility from filename/extension;
- create a second weaker staging/validation algorithm.

C4-I source-intake, held-descriptor, sidecar, two-pass digest staging and candidate
validation semantics remain the source of truth.

## 8. Future C4-II-B handoff

C4-II-B must treat the C4-II-A browser/session token as a reference only.

Before destructive execution it must:

```text
reopen launcher-private original path
→ compare C4-I SourceIdentity
→ recompute full SHA-256
→ re-check sidecars/self-containment
→ stage again
→ validate again
→ only then enter C4-I destructive execution
```

Any mismatch returns to selection.

## 9. Open product obligations after CR-011

- explicit bounded C4-II-A authorization;
- C4-II-A source-selection/validation implementation;
- C4-II-B destructive confirmation/execution integration;
- C4-II-C outcome/restart/support UX;
- C4-III end-to-end verification and lifecycle closure;
- macOS `.app`/`.dmg` packaging;
- safe packaged update flow;
- installation verification;
- full release-candidate smoke.

Do not collapse these into one broad PR.

## 10. Current next action

```text
Finish, validate and independently audit the CR-011 decision PR.
Do not implement C4-II-A on this branch.
After CR-011 merges, prepare a separate bounded C4-II-A authorization/task.
```