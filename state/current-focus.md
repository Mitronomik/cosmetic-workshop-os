# Current focus

Slice A4 is active.

## Active slice

**A4.3 — Contain responsive Clients workspace**

Runtime scope: frontend presentation containment for the existing `/clients` workspace only.

## Baseline memory

- PR #125 / A4.1 is merged and DONE.
- A4.1 merge commit: `50c44ff0919401d51c165d6ebec1266c688bfb08`.
- A4.1 runtime head: `effb5ee270c9fbddc777e57c41ad0b53acd77f9d`.
- PR #126 / A4.2 — Contain responsive Orders tables is merged and DONE.
- A4.2 merge commit: `4487e4044d89d88538226c5b36543e6009f279f9`.
- A4.2 runtime head: `010bd1bf3791dd6a6d754ea2ed0efdcd2ab564d3`.
- Product-owner manual responsive verification for A4.2 passed at `1440×900`, `1024×768`, `768×900`, and `390×844`.

## Boundaries

- Preserve existing Client, Client Wish, Client Feedback, and ClientRecipe behavior.
- No backend, API, schema, migration, validation contract, audit, lifecycle, mutation-guard, archive, wish-status, feedback, or ClientRecipe semantic changes.
- Prefer CSS-only containment; minimal client-page markup hooks are allowed when needed for scoped selectors.
- `/inventory` and `/packaging-items` remain future A4 follow-ups.
- Do not mark all of A4 complete.
