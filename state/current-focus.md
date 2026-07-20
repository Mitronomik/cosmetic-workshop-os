# Current focus

Slice A4 is active.

## Active slice

**A4.2 — Contain responsive Orders tables**

Runtime scope: frontend presentation containment for the existing `/orders` page only.

## Baseline memory

- PR #125 / A4.1 is merged.
- A4.1 merge commit: `50c44ff0919401d51c165d6ebec1266c688bfb08`.
- A4.1 runtime head: `effb5ee270c9fbddc777e57c41ad0b53acd77f9d`.
- A4.1 is DONE.

## Boundaries

- Preserve existing Order, Production Readiness, Production Confirmation, reconciliation, cancellation, and archiving behavior.
- No backend, API, schema, migration, validation, production, FEFO, stock, cost, tax, margin, or status transition changes.
- Prefer CSS-only containment.
- `/clients`, `/inventory`, and `/packaging-items` remain future A4 follow-ups.
- Do not mark all of A4 complete.
