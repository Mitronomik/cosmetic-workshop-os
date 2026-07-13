# Handoff

## Active branch

- Branch: `codex/user-facing-technical-copy-cleanup`
- Base: local `main` baseline `b44e6ab14f3afc5eed8dcccfb9a68789484a52be` (merge commit of PR #107). No newer local main commits were present; no remote named `origin` is configured in this checkout.
- Published head: pending until commit/PR publication.

## Changed runtime areas

- Topbar healthy/unavailable service copy.
- Import page explanatory copy and non-goal boundaries.
- Demo Data visible count labels and technical copy.
- Targeted route/capability copy in exports, reports/report documents, recipes, stock/inventory, demo data, onboarding/help text.

## Tests actually run

- Targeted source inventory/search before and after edits.
- `cd frontend && npm run build` — passed.
- `cd backend && python3 -m pytest` — failed: 5 failed, 463 passed; no backend files changed.
- `git diff --check` — passed.
- Partial Playwright/Chromium smoke against isolated database/user-data — completed for healthy state, unavailable state, Import intro copy, Demo Data raw-label absence, and route truth scan.

## Browser evidence

- Browser: headless Chromium from local Playwright install.
- Viewports: 1440×900 and 390×844.
- Isolated paths: `/tmp/cwo-a1-smoke-MxPIsh/smoke.sqlite`, `/tmp/cwo-a1-smoke-MxPIsh/user-data`.
- Screenshots: `/tmp/cwo-a1-smoke-MxPIsh/screens/healthy-desktop.png`, `demo-narrow.png`, `imports-desktop.png`, `unavailable.png`.
- Pending: full deterministic Import normal Apply, Apply-success-plus-refresh-failure, and structured conflict browser scenarios.

## Merge blockers

- Complete required focused browser smoke, especially the three Import mutation contract scenarios, or record external Hermes verification.
- Decide whether known backend pytest failures are acceptable as baseline failures for this frontend-only slice.

## Required next verification

Run the full Slice A1 browser smoke with isolated SQLite database and isolated user-data directory for healthy state, unavailable service, Import normal Apply, Import refresh-failure contract, Import conflict, Demo Data labels, route truth, and narrow keyboard behavior.

## Next slice

Slice A2 remains blocked until Slice A1 is merged and verified. No future PR number is assigned.
