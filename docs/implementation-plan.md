# cosmetic-workshop-os — Active implementation plan

Project: `cosmetic-workshop-os`
Client-facing name: **Мастерская косметолога**
Status: **active current implementation sequence**
Updated: `2026-08-08`

## Current lifecycle

```text
PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED
PR #179 — MERGED — A3 CLOSED / A4 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Merged baseline

```text
PR #178 reviewed A3 head — b0de148032d9b3d2f9912298897f8649c9b1692b
PR #178 merge — 9d95b0c39c4abd05d5a574c6cd8574b8e457f36b
PR #179 reviewed A3-closure/A4-auth head — 72b04510efd6d1f104369a450ed1c4d4dfe063ad
PR #179 merge — 52cc0b04e0b9531b6cc234c83cbcbb81e04a37bf
```

A3 final proof: 14 A3, 28 A2, 17 A1, 514 C4-I, 2457 full backend+launcher, native-picker smoke PASS, lifecycle PASS, independent P0=0/P1=0/P2=0.

## Current implementation window — C4-II-A4

Implement only the browser/session/presentation layer already selected by ADR 0018:

- launcher fragment handoff without mutating the ordinary runtime config;
- exact `/backups/restore` nested route and secondary entry from `/backups`;
- synchronous fragment capture/removal before the ordinary shell module;
- one-use bootstrap exchange;
- only `control_origin`, `run_id`, session token in `sessionStorage`;
- strict reload/retry metadata in same-tab `history.state`, never authority;
- heartbeat and state polling;
- exact DTO allowlists and pathless presentation;
- select/cancel/reselect over existing A2 only;
- Russian human-readable non-destructive UX;
- cross-layer A4→A2→A3→A1/C4-I smoke.

## Mandatory A4 seams

### Browser/filesystem seam

No browser-controlled `path`, `source_path`, file bytes, upload/blob, bookmark/handle or `<input type="file">`. Native picker and absolute path remain launcher-owned.

### Session/replay seam

The one-use bootstrap secret exists only in the launch fragment until exchange. The session token lives only in `sessionStorage` and Authorization headers. Non-secret command replay metadata may live in `history.state` only to preserve exact A2 idempotency across reload/network uncertainty. Missing replay after prior activity must fail closed; it must never guess a sequence.

### A4→C4-II-B seam

A4 is non-destructive. Accepted validation is not Restore authorization. No `execute_restore`, confirmation, durable Restore phase, `before_restore` safety copy, database replacement/migration, rollback/recovery mutation or Restore AuditLog.

## Required A4 proof

At minimum prove:

1. launcher handoff is fragment-only and original config remains unchanged;
2. handoff failure closes control authority but ordinary product still opens;
3. fragment is removed before shell route processing;
4. sessionStorage contains only the three approved descriptors;
5. no localStorage/query/file-input/path fallback;
6. unknown/path-bearing DTO fields are rejected;
7. 15-second heartbeat and 60-second server expiry contract remain aligned;
8. random request ID is 128 bits and command sequence is strict;
9. network uncertainty retries exact same request ID/sequence;
10. reload recovers sequence only from same-tab replay or pristine `idle/generation=0` proof;
11. invalid session/run mismatch clears descriptors;
12. `/backups/restore` is human-readable, keyboard reachable and narrow-screen usable;
13. accepted state clearly says working data is unchanged and Restore has not started;
14. `frontend/src/main.ts` remains byte-identical;
15. A3/A2/A1/C4-I and broader regressions remain green;
16. cross-layer smoke proves no source/working-DB/AuditLog/durable-Restore mutation.

## Exact-head gate

```text
git status --short
→ git diff --check 52cc0b04e0b9531b6cc234c83cbcbb81e04a37bf...HEAD
→ python3 scripts/check_documentation_lifecycle.py
→ cd frontend && npm run build && npm run test:restore-control
→ launcher A4 targeted tests
→ A3/A2/A1/C4-I regressions
→ full backend + launcher suite
→ relevant frontend regression suite
→ python3 scripts/smoke_restore_browser_session.py --expected-head <HEAD>
→ desktop/narrow/keyboard smoke of /backups and /backups/restore
→ clean status/head
→ independent P0=0/P1=0/P2=0
```

No PASS is claimed until this runs on the final published A4 head.

## Forbidden scope

No destructive C4-II-B, backend Restore mutation endpoint, WebSocket/generic launcher server, packaging redesign, cloud sync, OCR, roles/multiuser or advanced analytics.

## Next action

Finish A4 self-audit → open Draft PR → run exact-head build/tests/smoke/UI review → resolve every P0/P1/P2 → merge only after complete evidence → post-merge lifecycle/authorization decision before C4-II-B.
