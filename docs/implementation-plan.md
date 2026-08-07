# cosmetic-workshop-os — Active implementation plan

Project: `cosmetic-workshop-os`
Client-facing name: **Мастерская косметолога**
Status: **active current implementation sequence**
Updated: `2026-08-08`

Historical pre-compaction plan remains byte-identical at
`docs/history/implementation-plan/2026-08-06-pre-compaction.md`.

## 1. Source of truth

1. applicable `AGENTS.md`;
2. newest accepted ADR for the exact topic;
3. `docs/current-lifecycle.md`;
4. unsuperseded durable ADR semantics;
5. `docs/restore-interaction-and-validation-session.md`;
6. `docs/c4-ii-a-implementation-slices.md`;
7. this plan;
8. active `state/` files;
9. `docs/history/` evidence.

## 2. Merged baseline

```text
PR #170 / C4-I merge — e6997281d2e0268ce54184d988c114bac71c35e2
PR #171 merge — 76ab59216047222714a32f2793a789b3dc8df19a
PR #172 / CR-011 merge — 998596560db6780a677bdec363d1fd19db30c1b6
PR #173 / sliced authorization merge — aaedf2735660fb92eb627f7eeab327437d459b56
PR #174 / A1 merge — 504e776508c940554b3ee8659a201af21db8303c
```

A1 reviewed head:
`e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5`.

A1 exact-head evidence: lifecycle PASS, real-service smoke PASS, 17 targeted tests
passed, 514 existing C4-I Restore tests passed, 2415 backend+launcher tests passed,
P0=0 / P1=0 / P2=0.

## 3. Current lifecycle

```text
PR #174 — MERGED — C4-II-A1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

A2 runtime implementation may start only after this post-A1 closure changeset is
merged to `main`.

## 4. Current implementation window — C4-II-A2

Goal: implement the exact-run launcher-owned loopback control/session protocol
around the merged A1 service, without real picker, browser Restore workspace or
destructive Restore.

A2 owns:

- exact `127.0.0.1` + OS-assigned ephemeral port;
- exact Host and configured local frontend Origin enforcement;
- one-use >=256-bit bootstrap capability with atomic consume;
- separate >=256-bit run-scoped session token;
- `Cache-Control: no-store`;
- 15-second heartbeat / 60-second authenticated inactivity expiry;
- concurrent HTTP servicing;
- >=128-bit request ID + strict monotonic `command_seq`;
- sequence consumption before business preconditions;
- idempotent retry and stale/future replay rejection;
- A1 generation/cancel/invalidation integration;
- launcher-owned control-plane start/stop lifecycle;
- source-selection adapter boundary.

## 5. Mandatory transitional seams

### A2→A3

Production A2 must use a launcher-owned adapter that returns typed
`picker_unavailable`. It obtains no filesystem path.

Tests may inject a launcher-owned fake adapter directly in launcher/control code.
The browser may never supply `path`, `source_path`, upload/blob, file bytes,
file handle/bookmark or other filesystem authority. No production test-bypass or
generic filesystem/shell/SQL route is allowed.

### A2→A4

Production browser navigation remains unchanged. A2 must not append the bootstrap
fragment to the real product browser URL. The first production browser handoff is
A4 scope, together with fragment consumption/removal and `sessionStorage`.

A2 smoke therefore uses a direct authenticated local HTTP client.

## 6. Command sequencing contract

For mutating commands:

```text
Host/Origin/auth/syntax validation
→ verify expected next command_seq
→ atomically bind sequence to request ID
→ consume expected sequence
→ evaluate business preconditions
→ return/cache typed result
```

Auth/syntax-invalid requests do not consume sequence. A valid expected-next
command consumes it before business evaluation, including typed business
rejection. Same sequence + same request ID may replay cached result; same sequence
+ different request ID, stale or future sequence fails closed.

## 7. Concurrency and expiry contract

Long selection/validation work must not block the only HTTP servicing loop.
Heartbeat/state/cancel remain serviceable while a worker is in flight.

Session expiry invalidates session token, A1 generation and retained proof.
Cleanup waits for the owning worker to quiesce; cancellation must not delete
scratch out from under active A1 work.

## 8. A2 forbidden scope

Do not implement:

- real `/usr/bin/osascript` picker;
- `/backups/restore` or frontend Restore UI;
- production browser bootstrap-fragment handoff;
- destructive Restore confirmation/execute command;
- `execute_restore(...)`;
- durable Restore operation/phase or `before_restore` safety copy;
- working DB replacement/migration;
- rollback/startup-recovery mutation;
- Restore AuditLog;
- ordinary FastAPI Restore mutation endpoint;
- WebSocket or generic localhost command server;
- new dependency or packaging implementation.

## 9. Required A2 tests

At minimum cover:

1. loopback-only ephemeral bind;
2. Host/Origin rejection;
3. no wildcard CORS/cookie authority;
4. bootstrap one-use under concurrency;
5. token entropy/run scoping;
6. no-store responses;
7. heartbeat and 60s expiry;
8. concurrent heartbeat/state/cancel during long fake work;
9. invalid auth/syntax does not consume sequence;
10. typed business rejection consumes valid next sequence;
11. idempotent same request-ID retry;
12. different request ID/stale/future sequence rejection;
13. duplicate concurrent select rejection;
14. cancel/expiry/reselection clears A1 proof/generation;
15. production `picker_unavailable` returns no path;
16. request/browser DTO has no path/file authority;
17. real production browser URL remains unchanged;
18. no durable Restore/safety-copy/AuditLog/working-DB mutation;
19. A1 + C4-I regressions remain green.

## 10. Exact-head verification gate

Run on the final A2 head:

```text
git status --short
→ git diff --check <A2-base>...HEAD
→ python3 scripts/check_documentation_lifecycle.py
→ targeted A2 tests
→ A1 + existing C4-I Restore regression tests
→ python3 -m pytest backend/app/tests launcher/tests
→ exact-head direct-local-HTTP A2 smoke
→ verify clean status again
→ independent exact-head code/architecture audit
→ P0=0 / P1=0 / P2=0
```

## 11. Successor gates

A3 remains blocked until A2 passes its exact-head gate, merges, and lifecycle is
closed from updated `main`. A4 remains blocked by A3. C4-II-B destructive
confirmation/execution remains separately not authorized.

## 12. Current next action

```text
merge post-A1 lifecycle closure
→ create fresh A2 branch from updated main
→ implement only exact-run launcher control plane
→ exact-head tests + direct local HTTP smoke + independent audit
```
