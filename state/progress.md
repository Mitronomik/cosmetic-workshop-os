# Progress

Updated: `2026-08-06`

Current lifecycle authority: `docs/current-lifecycle.md`.

## Completed

- C1 — completed.
- C2 — completed.
- C3 — completed, merged, exact-head verified, and hardened.
- CR-010 — launcher-assisted Restore semantics accepted.
- C4-I — launcher-owned Restore safety engine:
  `DONE — MERGED AND EXACT-HEAD VERIFIED`.
- PR #170 final reviewed head:
  `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8`.
- PR #170 merge commit:
  `e6997281d2e0268ce54184d988c114bac71c35e2`.
- Six independent C4-I audit rounds closed twenty-four findings.
- Curated C4-I history is retained in
  `docs/history/c4-i-implementation-and-audit-history.md`.
- A broader project timeline is retained in
  `docs/history/project-timeline-through-pr170.md`.
- The complete pre-compaction implementation plan and state snapshots are
  preserved byte-for-byte under `docs/history/`.
- The detailed pre-compaction change-request ledger is preserved byte-for-byte
  at `docs/history/change-requests/2026-08-06-pre-compaction.md`.
- The active change-request ledger now includes CR-011 explicitly.
- `docs/current-lifecycle.md` records the current authority order and the
  explicit supersession map for dated C4 status prose.
- `scripts/check_documentation_lifecycle.py` provides a repeatable documentation
  consistency check.

## Current authorized work

```text
CR-011 — Launcher Restore interaction and validation-session boundary
AUTHORIZED — DECISION ONLY — NOT DECIDED
```

CR-011 must select one concrete, testable interaction architecture. No runtime
implementation is authorized by the current documentation PR.

## Planned but blocked

```text
C4-II-A — PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III  — PLANNED — NOT AUTHORIZED
```

## Open product obligations

- user-facing Restore;
- macOS packaging;
- safe packaged update flow;
- installation verification;
- full release-candidate smoke;
- continuing documentation accuracy;
- focused synchronization of dated lifecycle paragraphs in
  `docs/architecture.md`, `docs/roadmap.md`, and `docs/backup-and-restore.md`
  when those large documents next receive a bounded maintenance pass.

Until that focused pass, their stale lifecycle labels are explicitly superseded
by `docs/current-lifecycle.md`; their product and safety contracts remain valid.

## Current product truth

```text
C4 — ACTIVE
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Validation-session boundary required before C4-II-A

Future source selection and validation presentation must be launcher-owned and
non-destructive. It must not:

- call `execute_restore(...)`;
- create a durable Restore operation record;
- enter any Restore phase;
- create a `before_restore` safety copy;
- replace or migrate the working database;
- perform rollback or recovery mutation;
- write a Restore AuditLog event;
- expose the absolute selected-source path as browser authority.

C4-II-B must later re-prove source or retained-candidate identity. An opaque
session token is a reference to launcher-owned state, not validation authority.

## Not started

No native picker, launcher IPC, loopback control plane, WebSocket, frontend
Restore UI, FastAPI Restore endpoint, browser-upload Restore path,
validation-session service, packaging change, or destructive execution is
implemented or authorized.

## Required documentation check

```bash
python3 scripts/check_documentation_lifecycle.py
```

This check is documentation-only and is not product smoke.
