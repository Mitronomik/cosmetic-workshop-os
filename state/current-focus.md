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
