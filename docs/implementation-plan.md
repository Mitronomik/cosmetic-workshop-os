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
PR #175 / A1 closure + A2 authorization merge — 636645ece744752f6a753ae5a25a05297fd34e10
```

A1 reviewed head `e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5` passed
lifecycle/smoke, 17 targeted tests, 514 C4-I Restore tests, 2415 full
backend+launcher tests and P0=0 / P1=0 / P2=0.

## 3. Current lifecycle

```text
PR #174 — MERGED — C4-II-A1 EXACT-HEAD VERIFIED
PR #175 — MERGED — A1 CLOSED / A2 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## 4. Current implementation window — C4-II-A2

Goal: implement the exact-run launcher-owned loopback control/session protocol
around merged A1 without real picker, browser Restore workspace or destructive
Restore.

Implemented in the current changeset:

- `launcher/restore/control_protocol.py` — safe DTOs and launcher-owned picker seam;
- `launcher/restore/control_session.py` — one-use bootstrap, run session,
  `command_seq`, liveness/expiry and worker-generation coordination;
- `launcher/restore/control_plane.py` — exact loopback stdlib HTTP server;
- exact `127.0.0.1` + OS-assigned ephemeral port;
- exact Host and configured local frontend Origin;
- one-use >=256-bit bootstrap capability and >=256-bit session token;
- no wildcard CORS, no cookie session, `Cache-Control: no-store`;
- 15-second heartbeat / 60-second authenticated inactivity expiry;
- concurrent request servicing during one selection/validation worker;
- >=128-bit request-ID namespace + strict monotonic `command_seq`;
- expected-next sequence consumed before business preconditions;
- idempotent same-request retry and stale/future/conflict rejection;
- A1 generation/cancel/proof invalidation;
- runtime lifecycle wiring after proved backend start and before backend stop;
- exact-head direct-local-HTTP smoke with injected launcher-owned fake picker and
  real A1/C4-I validation.

## 5. Mandatory transitional seams

### A2→A3

Production A2 uses `UnavailableSourceSelectionAdapter` and returns typed
`picker_unavailable`; it obtains no filesystem path.

Tests/smoke may inject a launcher-owned fake adapter directly. Browser/control
payload cannot provide `path`, `source_path`, file bytes, upload/blob,
handle/bookmark or equivalent filesystem authority. Select/cancel schema is only
`request_id` + `command_seq`.

### A2→A4

Production browser navigation remains unchanged. `open_runtime_browser(...)` does
not append `#cw-control`, control port, bootstrap capability or session token. A4
owns the first production fragment handoff, consumer/removal, `sessionStorage`
and `/backups/restore`.

A2 smoke uses a direct authenticated local HTTP client.

## 6. Command sequencing contract

For mutating commands:

```text
Host/Origin/auth/JSON/schema validation
→ reject stale/future/conflicting sequence
→ atomically bind exact expected next sequence to request ID + command
→ consume sequence
→ evaluate business preconditions
→ retain safe in-progress/final result
```

Invalid transport/auth/schema/sequence requests do not consume sequence. A valid
expected-next command does, including `action_in_progress` and other typed
business refusals. Same current sequence + same request ID + same command returns
the retained safe result; any other replay fails closed.

## 7. Concurrency and expiry contract

Long selection/validation runs on one launcher-owned worker, not the only HTTP
request loop. Heartbeat/state/cancel remain serviceable. Cancel/expiry/reselection
invalidate browser session/A1 authority immediately and generation-gate late
publication. Final cleanup waits for worker quiescence.

## 8. A2 forbidden scope

Do not implement:

- real `/usr/bin/osascript` picker, `shell=True` or A3 picker worker;
- `/backups/restore` or frontend Restore UI;
- production browser bootstrap-fragment handoff;
- destructive Restore confirmation/execute command or `execute_restore(...)`;
- durable Restore phase/state or `before_restore` safety copy;
- working DB replacement/migration, rollback/recovery mutation or Restore AuditLog;
- ordinary FastAPI Restore mutation endpoint;
- WebSocket or generic localhost command server;
- new dependency or packaging implementation.

## 9. Required A2 tests

At minimum cover:

1. loopback-only ephemeral bind;
2. exact Host/Origin and narrow CORS;
3. atomic one-use bootstrap race;
4. token entropy/run scoping and no-store;
5. heartbeat/60s expiry;
6. concurrent heartbeat/state/cancel while fake long work runs;
7. invalid auth/Host/Origin/schema/sequence does not consume sequence;
8. valid business rejection consumes expected sequence;
9. idempotent retry plus conflict/stale/future refusal;
10. duplicate select returns consumed `action_in_progress`;
11. cancel/expiry/reselection clears A1 proof/generation;
12. production `picker_unavailable` obtains no path;
13. request/control state exposes no path/file authority;
14. production browser URL remains unchanged;
15. runtime ordering backend→control→browser and control→backend on shutdown;
16. no durable Restore/safety-copy/AuditLog/working-DB mutation;
17. A1 + C4-I regressions remain green.

## 10. Exact-head verification gate

Run on the final A2 head:

```text
git status --short
→ git diff --check 636645ece744752f6a753ae5a25a05297fd34e10...HEAD
→ python3 scripts/check_documentation_lifecycle.py
→ targeted A2 protocol/security/concurrency/runtime tests
→ A1 validation-session tests
→ existing C4-I Restore regression tests
→ python3 -m pytest backend/app/tests launcher/tests
→ python3 scripts/smoke_restore_control_plane.py --expected-head <HEAD>
→ verify clean status/head again
→ independent exact-head code/architecture audit
→ P0=0 / P1=0 / P2=0
```

No PASS is claimed until run on the exact published head.

## 11. Successor gates

A3 remains blocked until A2 passes exact-head verification, merges and lifecycle
is closed from updated `main`. A4 remains blocked by A3. C4-II-B destructive
confirmation/execution remains separately not authorized.

## 12. Current next action

```text
finish A2 implementation audit
→ open draft PR
→ run exact-head tests + direct local HTTP smoke
→ resolve every P0/P1/P2 finding
→ merge only after complete evidence
→ close A2 lifecycle before A3
```
