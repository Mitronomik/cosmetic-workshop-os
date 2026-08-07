# Current focus — PR #171 documentation closure gate

Updated: `2026-08-07`

Current lifecycle authority:
[`docs/current-lifecycle.md`](../docs/current-lifecycle.md).

Current decision:
[`docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md`](../docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md).

Current change-request ledger:
[`state/change-requests.md`](change-requests.md).

Searchable project history:
[`docs/history/README.md`](../docs/history/README.md).

## Current lifecycle

```text
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — AUTHORIZED — DECISION ONLY — NOT DECIDED
C4-II-A — PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Current action while PR #171 is open

PR #171 is the current task.

```text
finish independent documentation/architecture audit
→ correct every finding
→ run documentation checks in a real checkout
→ repeat exact-head read-only gate
→ merge PR #171
```

Do not start CR-011 from the unmerged PR #171 branch.
Do not create a dependent CR-011 branch from the PR #171 head.
No runtime implementation is authorized in this branch.

## Authorized successor after PR #171 merges

After PR #171 merges, update `main` and create a fresh branch from merged `main`.
Only then begin:

```text
CR-011 — Decide the launcher Restore interaction and validation-session boundary.
Decision-only. No runtime implementation is authorized.
```

CR-011 must select one concrete architecture for screen ownership, native picker
ownership, browser-to-launcher command path if any, exact-run authentication,
origin/replay/stale-session protection, path privacy, backend lifecycle,
dependencies, packaging consequences, cleanup, and exact-head smoke.

## Blocked until CR-011 is accepted

No agent may implement:

- a native picker;
- launcher IPC or WebSocket communication;
- a loopback control endpoint;
- a FastAPI Restore endpoint;
- SPA-owned filesystem access;
- browser upload as the authoritative Restore source;
- frontend Restore controls;
- a validation-session Python service;
- packaging changes for Restore;
- C4-II-A, C4-II-B, C4-II-C, or C4-III runtime work.

## Mandatory future validation-session semantics

Future C4-II-A must use a launcher-owned non-destructive boundary conceptually
represented as `prepare_restore_candidate(...)`.

It must not call `execute_restore(...)`, create a durable Restore operation,
enter a Restore phase, create a `before_restore` safety copy, mutate or migrate
the working database, perform rollback/recovery mutation, write a Restore
AuditLog event, or give the browser authority over the selected-source path.

C4-II-B must later re-prove source or retained-candidate identity through
launcher-owned state and accepted C4-I rules before destructive execution.

## Documentation verification

Before PR #171 can merge, run in a real checkout:

```bash
git diff --check
python3 scripts/check_documentation_lifecycle.py
```

Also run the repository Markdown/link check if one is defined, then repeat the
independent exact-head read-only audit.