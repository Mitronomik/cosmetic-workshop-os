# Progress

Updated: `2026-08-07`

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
- Searchable project history and exact pre-compaction snapshots are preserved
  under `docs/history/`.
- The compact active change-request ledger includes CR-011.
- `docs/current-lifecycle.md` defines scope-and-recency authority and explicitly
  supersedes dated lifecycle wording in ADR 0016, architecture, roadmap, and
  backup/restore docs without revoking their durable contracts.
- Historical Git guidance now uses read-only `git show` / separate worktree
  patterns rather than replacing active files.

## Current lifecycle

```text
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — AUTHORIZED — DECISION ONLY — NOT DECIDED
C4-II-A — PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Current work — PR #171 closure

PR #171 remains the current task until it is independently verified and merged.

Required sequence:

```text
correct audit findings
→ run documentation checks in a real checkout
→ repeat exact-head read-only gate
→ merge PR #171
```

Do not start CR-011 from the unmerged PR #171 branch.
Do not create a dependent CR-011 branch from the PR #171 head.

## Authorized successor after PR #171 merges

Only after PR #171 merges, update `main`, create a new branch from merged `main`,
and begin:

```text
CR-011 — Launcher Restore interaction and validation-session boundary
AUTHORIZED — DECISION ONLY — NOT DECIDED
```

CR-011 must select one concrete, testable interaction architecture. It does not
authorize runtime implementation.

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
- focused synchronization of dated lifecycle paragraphs in large reference
  documents when those files next receive bounded maintenance.

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

## Required documentation checks before PR #171 merge

```bash
git diff --check
python3 scripts/check_documentation_lifecycle.py
```

Also run the project Markdown/link check if defined. These checks are
Level 0 documentation verification and are not product smoke.