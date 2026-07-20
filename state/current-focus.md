# Current focus

Slice A4 is active.

## Active slice

**A4.4a — Contain responsive Inventory workspace**

Runtime scope: frontend presentation containment for the existing read-only `/inventory` workspace only.

## Baseline memory

- PR #125 / A4.1 is merged and DONE.
- A4.1 merge commit: `50c44ff0919401d51c165d6ebec1266c688bfb08`.
- A4.1 runtime head: `effb5ee270c9fbddc777e57c41ad0b53acd77f9d`.
- PR #126 / A4.2 — Contain responsive Orders tables is merged and DONE.
- A4.2 merge commit: `4487e4044d89d88538226c5b36543e6009f279f9`.
- A4.2 runtime head: `010bd1bf3791dd6a6d754ea2ed0efdcd2ab564d3`.
- Product-owner manual responsive verification for A4.2 passed at `1440×900`, `1024×768`, `768×900`, and `390×844`.
- PR #127 / A4.3 — Contain responsive Clients workspace is merged and DONE.
- A4.3 merge commit: `255703d26d9e166f00f2c9ba3030cf4bc41fe044`.
- A4.3 runtime head: `1f6930d8f2e3367372a384a51e7d04a3a7c96bee`.
- Product-owner manual exact-head smoke for A4.3 passed.

## Boundaries

- Preserve existing Inventory overview metrics, ingredient-lot balance information, packaging balance information, and read-only behavior.
- No backend, API, schema, migration, stock movement, lot, packaging balance, FEFO, production, order, alert, purchase, or inventory-domain changes.
- Prefer CSS-only containment; minimal Inventory-specific markup hooks are allowed when needed for scoped selectors.
- `/packaging-items` remains a separate A4.4b follow-up.
- Do not mark all of A4 complete.
