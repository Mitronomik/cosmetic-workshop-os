# Project history index

Status: **HISTORICAL INDEX — NON-NORMATIVE**

This directory preserves searchable project history without allowing dated
branch-era instructions to override current architecture or lifecycle decisions.
Current lifecycle authority is `docs/current-lifecycle.md`.

## Authority rule

Historical records are evidence and context only. They never override:

1. `AGENTS.md` and nested `AGENTS.md` files;
2. accepted ADRs;
3. `docs/current-lifecycle.md`;
4. current normative architecture/profile documents;
5. `docs/implementation-plan.md`;
6. active `state/` files.

Every historical snapshot must be read in the context of its date. Status lines
such as `NOT MERGED`, `IN PROGRESS`, or `NEXT ACTION` describe that historical
moment and are not current instructions.

## Preserved records

### Curated histories

- [`project-timeline-through-pr170.md`](project-timeline-through-pr170.md) —
  major product, architecture, implementation, audit, and release-gate events
  through PR #170.
- [`c4-i-implementation-and-audit-history.md`](c4-i-implementation-and-audit-history.md)
  — six C4-I audit rounds and all twenty-four closed findings.

### Exact pre-compaction snapshots

The following files are preserved byte-for-byte from merge commit
`e6997281d2e0268ce54184d988c114bac71c35e2`:

- [`implementation-plan/2026-08-06-pre-compaction.md`](implementation-plan/2026-08-06-pre-compaction.md)
- [`state-snapshots/2026-08-06-c4-i-closure/current-focus.md`](state-snapshots/2026-08-06-c4-i-closure/current-focus.md)
- [`state-snapshots/2026-08-06-c4-i-closure/progress.md`](state-snapshots/2026-08-06-c4-i-closure/progress.md)
- [`state-snapshots/2026-08-06-c4-i-closure/handoff.md`](state-snapshots/2026-08-06-c4-i-closure/handoff.md)

The detailed change-request ledger that existed immediately before its active
compaction in PR #171 is preserved byte-for-byte at:

- [`change-requests/2026-08-06-pre-compaction.md`](change-requests/2026-08-06-pre-compaction.md)

These snapshots contain valuable implementation contracts, evidence, audit
detail, known limitations, accepted decisions, historical next actions, and
superseded lifecycle statements.

## Safe Git archaeology

For read-only inspection, prefer `git show` or a detached worktree:

```bash
git show e6997281d2e0268ce54184d988c114bac71c35e2:docs/implementation-plan.md

git worktree add \
  ../cosmetic-workshop-os-history-pr170 \
  e6997281d2e0268ce54184d988c114bac71c35e2
```

Do not use `git restore --source=<old-commit>` in the active development
checkout merely to inspect history: it replaces working-tree files and can
silently reintroduce obsolete active instructions.

## Compaction policy

When an active document becomes too large:

1. preserve the complete pre-compaction version under `docs/history/`;
2. mark it historical and non-normative through this index or a wrapper record;
3. keep the active document compact and current;
4. create or update a curated timeline when the removed detail contains
   decisions, known limitations, test evidence, audit findings, or rationale;
5. synchronize every active document that carries the affected lifecycle status;
6. update `docs/current-lifecycle.md` and its explicit supersession map when a
   large document cannot be safely rewritten in the same bounded PR;
7. verify that current repository search does not return contradictory compact
   active instructions.

Git history alone is a technical recovery mechanism. It is not a substitute for
searchable project memory in an agent-driven repository.
