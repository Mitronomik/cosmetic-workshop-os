# Progress

Updated: `2026-08-06`

> This is the current progress summary. The detailed pre-closure journal remains
> available in Git history at parent commit
> `e6997281d2e0268ce54184d988c114bac71c35e2`.

## Current phase

```text
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4 — ACTIVE

C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A — AUTHORIZED — NOT IMPLEMENTED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED

Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## C4-I merge closure

- Pull request: **#170 — `C4-I — Implement launcher-owned Restore safety engine`**
- State: **MERGED**
- Final independently reviewed and exact-head-tested implementation head:
  `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8`
- Merge commit on `main`:
  `e6997281d2e0268ce54184d988c114bac71c35e2`
- The reviewed head is a parent of the merge commit.
- The merge commit adds no file change beyond the reviewed head.
- Accepted exact-head evidence belongs to PR #170 and is not re-executed by this
  documentation-only lifecycle closure.

C4-I delivered only internal launcher infrastructure. It did not deliver a
user-facing Restore workflow, so Restore remains `NOT IMPLEMENTED`.

The accepted CR-010 / ADR 0016 safety contract remains unchanged: twelve phases,
unchanged transition graph, unchanged recovery matrix, unchanged
`replacement_intent` crash rule, no Restore AuditLog event and no running-backend
Restore endpoint.

## Documentation-only closure work

This lifecycle closure changes documentation and state only. It:

- records PR #170 as merged and exact-head verified;
- removes the obsolete current instruction to audit or merge PR #170;
- makes `C4-II-A` the only authorized next runtime slice;
- divides the remaining user-facing work into `C4-II-B` and `C4-II-C` without
  authorizing either;
- keeps `C4-III` planned and not authorized;
- keeps packaging, safe packaged updates, release smoke and release readiness
  open;
- changes no runtime, migration, dependency or test file.

## Next ready slice

```text
C4-II-A — Launcher Restore source selection and validation presentation
AUTHORIZED — NOT IMPLEMENTED
```

C4-II-A is non-destructive. It may select one local SQLite backup, invoke the
existing C4-I staging and validation contracts, and present human-readable
information and rejection outcomes. It must not execute Restore, create the
`before_restore` safety copy, replace or migrate the working database, run
rollback, add a FastAPI Restore endpoint, add an ordinary SPA mutation, add a
Restore AuditLog event, or change the accepted state machine.

## Known open obligations

- user-facing Restore execution and confirmation — not implemented;
- completion, rollback and support-assisted outcome UX — not implemented;
- complete Restore end-to-end verification and C4 closure — not completed;
- macOS package — not completed;
- safe packaged update flow — not completed;
- user/remote installation verification — not completed;
- full release-candidate smoke — not completed.
