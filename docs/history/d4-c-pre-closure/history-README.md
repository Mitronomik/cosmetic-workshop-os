# Documentation history

`docs/history/` contains immutable project evidence and pre-compaction/pre-decision snapshots. Historical status text is evidence of what was true at that time; it does not override `docs/current-lifecycle.md` or a newer accepted ADR.

## Current index

- `d4-b-pre-closure/` — exact active lifecycle/state/checker surfaces from merged head `d60a3be993c76b59292cf27ee66bcbe856669fc4` immediately before D4-B closure and D4-C authorization.
- `d4-a-pre-closure/` — exact active lifecycle/state/checker surfaces from merged head `89dd69dc1958e622146e01869cc34d4cd2ec859e` immediately before D4-A closure and D4-B authorization.
- `d4-pre-decision/` — exact active lifecycle/state/checker surfaces from `main` `dc2301f7d4e101ad0fba851325dae9274f02da0c` immediately before CR-013 / ADR 0020.
- `c4-iii-pre-closure/` — exact active surfaces immediately before C4-III lifecycle closure.
- `c4-iii-pre-partial-verification/` — checkpoint before partial C4-III verification state was compacted.
- `c4-ii-c-pre-closure/` — state before C4-II-C lifecycle closure.
- `c4-ii-c-pre-implementation/` — state before C4-II-C implementation.
- `c4-ii-b3-pre-closure/` — state before C4-II-B3 closure.
- `state-snapshots/2026-08-06-c4-i-closure/` — large state snapshots preserved at C4-I closure.
- `implementation-plan/2026-08-06-pre-compaction.md` — complete earlier implementation plan.
- `change-requests/2026-08-06-pre-compaction.md` — complete earlier change-request ledger.
- `project-timeline-through-pr170.md` and `c4-i-implementation-and-audit-history.md` — compact historical orientation.

## Rules

- Do not edit an exact snapshot to make it match current truth.
- Do not use historical `NOT AUTHORIZED`, `IN PROGRESS` or branch-era commands as current authority without checking `docs/current-lifecycle.md`.
- Before another active-document compaction, preserve the complete prior version here and update this index.
- Git history alone is not considered sufficient project memory.
