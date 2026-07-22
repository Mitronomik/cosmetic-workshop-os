# Current focus

## Baseline
- B3.1 shared feedback for Dashboard and Onboarding: DONE.
- Accepted B3.1 runtime head: `4eed8c2f64d7524607cf25fc696dd964c25213cc`.
- Merge commit / B3.2a base: `70bbc783452a373afba76bcd8f6fe94c1e7ac75b`.
- External exact-head smoke for B3.1: PASS — FULL AUTOMATED SMOKE PASSED.
- B1/B2 diagnostic conclusions remain authoritative.

## Active task
- PR #134 is the active B3.2a Alerts shared feedback lifecycle correction PR.
- Previous published head under review: `931d15c573cb821459fc4ef426cca88632c23f59`.
- Current correction status: implemented locally; publication is blocked in this runner because no `origin` remote is configured.
- Browser smoke remains pending after publication; PR #134 is not merge-ready until human review and external exact-published-head browser smoke pass.

## Scope
- Alerts-only shared feedback lifecycle for `/alerts`: route ownership, list reads, refreshes, filters, regeneration, resolve, dismiss, visible feedback, announcements, final focus recovery, invalid authoritative response recovery, all-control binding, and focused tests.

## Non-goals
- Do not implement `/purchase-suggestions` in this slice.
- Do not change backend alert rules, repositories, schemas, migrations, imports, backups, stock, orders, production, recipes, clients, or demo fixtures.
- Do not merge PR #134 or claim browser-smoke PASS in this correction.

## Next runtime slice
- B3.2b Purchases shared feedback lifecycle: NEXT separate slice after B3.2a review, publication, and smoke acceptance.
