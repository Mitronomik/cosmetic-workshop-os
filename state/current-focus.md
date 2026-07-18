# Current focus — Slice A3.5 Client Wishes structured validation

A3.4 / PR #118 is merged and verified: merge commit `1489b0f99602ef08fc1a11ab67549a954f80335d`, published head `1a5dcce9a919e2ad2fb803dacdc1608b7ff24a25`, local exact-head full automated smoke PASS.

Active slice: **A3.5 — Client Wishes structured validation**.

Scope is limited to the existing Client Wish create flow inside the client card (`POST /api/clients/{client_id}/wishes`) and its visible fields: `title`, `description`, `category`, `priority`, and `client_recipe_id`.

Excluded from this slice:
- Client Feedback validation or behavior changes;
- Client Wish edit semantics;
- Client Wish status/archive redesign;
- Orders;
- Production Readiness and Production Confirmation;
- schema, migration, dependency, CSS, CI, browser-dependency, and smoke-runner documentation changes.

No future PR number is assigned unless GitHub has already created the PR.

## 2026-07-18 — Current slice
- A3.5 Client Wish structured validation is DONE; merged at `e53e7852c8b384915fb77b59345170c43671151c` with verified runtime head `e19229df1afa74f4470864071e91a0e94a5631cd` and complete external exact-head smoke PASS.
- A3.6 Client Feedback structured validation is IN PROGRESS.
- Keep Orders, Production Readiness, and Production Confirmation as separate future slices.
