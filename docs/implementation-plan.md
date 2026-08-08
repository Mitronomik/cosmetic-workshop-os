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
PR #176 / A2 merge — 90a14dd9a11b83bc31a40e1d3fb9523f41772b88
```

A2 reviewed head `681cb4050bec082db6b637285590e232880af739` passed
lifecycle, stale-authority race regression 2/2, all A2 targeted 28/28, A1 17/17,
C4-I Restore 514/514, full backend+launcher 2443/2443, exact-head control-plane
smoke and independent audit P0=0 / P1=0 / P2=0.

## 3. Current lifecycle

```text
PR #176 — MERGED — C4-II-A2 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## 4. Closed A2 boundary

A2 is complete and remains the exact-run launcher control/session authority:
loopback-only ephemeral HTTP, exact Host/configured Origin, atomic bootstrap,
run-scoped session token, no-store/narrow CORS, 15s/60s liveness, monotonic
`command_seq`, one long-work owner, responsive state/heartbeat/cancel, A1 proof
invalidation and hardened stale A2→A1 begin race.

Production A2 still uses `UnavailableSourceSelectionAdapter`. Product browser URL
remains unchanged and carries no control bootstrap/session material.

## 5. Current implementation window — C4-II-A3

Goal: replace only the production `picker_unavailable` seam with the launcher-owned
native macOS picker selected in ADR 0018, then feed the chosen launcher-private
path through the existing A2 `SourceSelectionAdapter` and merged A1 validation.

Authorized implementation scope:

- owned short-lived `/usr/bin/osascript` child;
- macOS Standard Additions `choose file`;
- fixed AppleScript with no user-controlled interpolation;
- no `shell=True`;
- no `System Events`;
- typed user cancellation;
- absolute POSIX path returned only to launcher memory;
- process ownership, cancel/expiry termination and wait/quiescence;
- integration with existing A2 `SourceSelectionAdapter` only;
- selected path passed only to existing A1 `prepare_restore_candidate(...)`;
- no new Python/application dependency.

## 6. Mandatory A3 seams

### Browser/filesystem seam

Browser/control payload remains pathless. Do not add `path`, `source_path`, file
bytes, upload/blob, bookmark/handle or equivalent filesystem authority.

### A3→A4 seam

Production browser navigation remains unchanged. Do not append `#cw-control`,
control port, bootstrap capability or session token. Do not add `/backups/restore`.
A4 owns first production browser handoff and Restore UI.

### A3→C4-II-B seam

A3 is non-destructive. Do not add confirmation/execute, durable Restore phases,
`before_restore` safety copy, working-DB replacement/migration, rollback/recovery
mutation or Restore AuditLog.

## 7. Required A3 tests

At minimum cover:

1. exact executable is `/usr/bin/osascript`;
2. fixed Standard Additions `choose file` script;
3. no `shell=True`, `System Events` or user-script interpolation;
4. successful picker result returns a launcher-private absolute POSIX path;
5. ordinary user cancellation maps to typed cancellation, not technical failure;
6. cancel/expiry terminates owned picker child and waits for quiescence;
7. picker stderr/technical failure is mapped to safe typed failure with no raw path;
8. browser/control DTO stays pathless;
9. selected path flows through A2 adapter into real merged A1 validation;
10. A2 stale-worker/A1-proof hardening remains green;
11. production browser URL remains unchanged;
12. no destructive Restore state/safety-copy/AuditLog/working-DB mutation;
13. A2, A1 and C4-I regressions remain green.

Tests should inject process seams where needed; do not require an unattended test
to click a real GUI dialog.

## 8. Exact-head verification gate

Run on the final A3 head:

```text
git status --short
→ git diff --check <A3-base-main>...HEAD
→ python3 scripts/check_documentation_lifecycle.py
→ targeted A3 native-picker/process/cancel tests
→ A2 control/session/security/concurrency regressions
→ A1 validation-session regressions
→ existing C4-I Restore regressions
→ python3 -m pytest backend/app/tests launcher/tests
→ exact-head A3 integration smoke
→ verify clean status/head again
→ independent exact-head code/architecture audit
→ P0=0 / P1=0 / P2=0
```

## 9. Forbidden scope

Do not implement in A3:

- frontend `/backups/restore` or browser bootstrap-fragment handoff;
- browser filesystem fallback;
- destructive Restore confirmation/execution;
- backend Restore mutation endpoint;
- WebSocket/generic localhost command server;
- new dependency or packaging implementation;
- cloud sync, OCR, roles/multiuser or advanced analytics.

## 10. Successor gates

A4 remains blocked until A3 passes exact-head verification, merges and lifecycle
is closed from updated `main`. C4-II-B remains separately not authorized.

## 11. Current next action

```text
create small A3 runtime PR from post-#176 closure main
→ implement only native picker adapter/process ownership
→ targeted tests + exact-head smoke
→ full regression + independent audit
→ merge only at P0=0 / P1=0 / P2=0
→ close A3 lifecycle before A4
```
