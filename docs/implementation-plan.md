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
PR #174 / A1 merge — 504e776508c940554b3ee8659a201af21db8303c
PR #175 / A1 closure + A2 authorization — 636645ece744752f6a753ae5a25a05297fd34e10
PR #176 / A2 merge — 90a14dd9a11b83bc31a40e1d3fb9523f41772b88
PR #177 / A2 closure + A3 authorization — e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263
```

A2 reviewed head `681cb4050bec082db6b637285590e232880af739`
passed race 2/2, A2 28/28, A1 17/17, C4-I 514/514, full 2443/2443,
smoke and independent P0=0 / P1=0 / P2=0 audit.

PR #177 reviewed head `d767b957cb3debae584709f2bbadafebd8dd6a9e`
closed A2 lifecycle and authorized only A3.

## 3. Current lifecycle

```text
PR #176 — MERGED — C4-II-A2 EXACT-HEAD VERIFIED
PR #177 — MERGED — A2 CLOSED / A3 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## 4. Closed A2 boundary

A2 remains unchanged: exact loopback/Host/Origin, atomic bootstrap, run token,
no-store/narrow CORS, 15s/60s liveness, strict `command_seq`, one worker,
responsive heartbeat/state/cancel and hardened stale A2→A1 proof race.

The default unavailable adapter remains for direct/test construction. A3 is
wired only into production launcher startup.

## 5. Current implementation window — C4-II-A3

Goal: implement only the launcher-owned native macOS picker from ADR 0018.

Implemented in the current changeset:

- `launcher/restore/macos_picker.py`:
  - exact `OSASCRIPT_PATH = Path("/usr/bin/osascript")`;
  - fixed `use scripting additions` / `choose file` AppleScript;
  - no user-controlled AppleScript interpolation;
  - `shell=False`, no `System Events`;
  - typed user cancellation using AppleScript error `-128` → internal sentinel;
  - only absolute selected POSIX paths are returned;
  - A2 `cancel_event` polling;
  - owned terminate/reap, then kill/reap fallback;
  - non-macOS/missing helper → typed unavailable;
  - picker technical failures remain launcher-internal.
- `launcher/runtime.py`:
  - production-only injection of `MacOSNativeSourceSelectionAdapter()` into the
    existing `RestoreControlPlane`;
  - startup/recovery/control/browser/shutdown ordering otherwise unchanged.
- `launcher/restore/control_protocol.py` / `launcher/restore/__init__.py`:
  - documentation/export alignment only; A2 default unavailable seam retained.
- targeted A3 tests and `scripts/smoke_restore_native_picker.py`.

## 6. Mandatory A3 seams

### Browser/filesystem seam

Browser/control payload remains pathless. No `path`, `source_path`, file bytes,
upload/blob, bookmark/handle or equivalent filesystem authority.

### A3→A4 seam

Production browser navigation remains unchanged. No `#cw-control`, control port,
bootstrap capability, session token or `/backups/restore`. A4 owns those.

### A3→C4-II-B seam

A3 is non-destructive. No confirmation/execute, durable Restore phases,
`before_restore` safety copy, working-DB replacement/migration,
rollback/recovery mutation or Restore AuditLog.

## 7. Required A3 proof

At minimum prove:

1. exact `/usr/bin/osascript` production helper;
2. fixed Standard Additions `choose file` script;
3. no shell/System Events/user interpolation;
4. successful result is launcher-private absolute POSIX path;
5. user cancel is typed cancellation;
6. cancel and 60s expiry terminate/reap the owned picker child;
7. stubborn child reaches kill fallback and is reaped;
8. technical picker failure reaches safe A2 failure without stderr/path exposure;
9. browser/control DTO remains pathless;
10. production runtime injects A3 without changing A2 default test seam;
11. selected path goes through real A2 coordinator into real A1 validation;
12. A2 stale-worker proof hardening remains green;
13. product browser URL remains unchanged;
14. source/working DB/durable Restore state remain non-destructively unchanged;
15. A2/A1/C4-I/full regressions remain green.

## 8. Exact-head verification gate

Run on the final A3 head:

```text
git status --short
→ git diff --check e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263...HEAD
→ python3 scripts/check_documentation_lifecycle.py
→ python3 -m pytest launcher/tests/test_restore_native_picker*.py
→ python3 -m pytest launcher/tests/test_restore_control_*.py
→ python3 -m pytest launcher/tests/test_restore_validation_session.py
→ existing C4-I Restore regression
→ python3 -m pytest backend/app/tests launcher/tests
→ python3 scripts/smoke_restore_native_picker.py --expected-head <HEAD>
→ verify clean status/head again
→ independent exact-head audit
→ P0=0 / P1=0 / P2=0
```

No PASS is claimed until run on the exact published head.

## 9. Forbidden scope

Do not implement in A3:

- frontend `/backups/restore` or production fragment handoff;
- browser filesystem fallback;
- destructive Restore confirmation/execution;
- backend Restore mutation endpoint;
- WebSocket/generic launcher command server;
- new dependency or packaging implementation;
- cloud sync/OCR/roles/advanced analytics.

## 10. Successor gates

A4 remains blocked until A3 passes exact-head verification, merges and lifecycle
is closed from updated `main`. C4-II-B remains separately not authorized.

## 11. Current next action

```text
finish A3 implementation self-audit
→ open draft A3 PR
→ run exact-head A3/A2/A1/C4-I/full tests + native-picker smoke
→ resolve every P0/P1/P2 finding
→ merge only after complete evidence
→ close A3 lifecycle before A4
```
