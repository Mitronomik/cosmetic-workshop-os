# Current focus

## Baseline
- B3.1 shared feedback for Dashboard and Onboarding: DONE.
- Accepted B3.1 runtime head: `4eed8c2f64d7524607cf25fc696dd964c25213cc`.
- Merge commit / local implementation base: `70bbc783452a373afba76bcd8f6fe94c1e7ac75b`.
- External exact-head smoke for B3.1: PASS — FULL AUTOMATED SMOKE PASSED.
- B1/B2 diagnostic conclusions remain authoritative.
- Managed runner had no `origin` remote; product owner independently verified GitHub `main` is identical to `70bbc783452a373afba76bcd8f6fe94c1e7ac75b`.

## Active task
- B3.2a Alerts shared feedback lifecycle: ACTIVE for local implementation and human diff review.
- No future PR number is assigned.

## Scope
- Alerts-only shared feedback lifecycle for `/alerts`: list reads, refreshes, filters, regeneration, resolve, dismiss, route ownership, visible feedback, announcements, focus recovery, all-control binding, and focused tests.

## Non-goals
- Do not implement `/purchase-suggestions` in this slice.
- Do not change backend alert rules, repositories, schemas, migrations, imports, backups, stock, orders, production, recipes, clients, or demo fixtures.
- Do not push, create a PR, call `make_pr`, or claim exact-published-head smoke.

## Next runtime slice
- B3.2b Purchases shared feedback lifecycle: NEXT separate slice after B3.2a human review/publication.
