# Current Focus

## Slice A1a — focused technical copy cleanup

Exact scope:
- remove the permanent healthy local-service availability badge from normal operation;
- keep an unavailable-state Russian recovery message without API/backend/internal wording;
- update only the introductory `/imports` copy to describe CSV/XLSX → draft → preview/validation → confirmation → Apply → working records;
- map visible `/demo-data` count keys to Russian product labels with unknown keys shown as «Другие данные».

Non-goals:
- no A1b copy cleanup for exports, backups, reports, recipes, inventory, Help, Settings, dashboard capability cards, route readiness metadata, navigation statuses, or planned modules;
- no backend, API, schema, migration, CSS, dependency, polling, retry, import behavior, demo behavior, or state-transition changes.

Tests/checks for this slice:
- `git diff --check`;
- `git diff --name-only`;
- `git diff --stat`;
- `git status --short`;
- `cd frontend && npm run build`;
- `cd backend && python3 -m pytest`;
- focused source diff review for Import Apply identifiers;
- focused browser smoke at 1440×900 and 390×844 if local browser tooling is available.

Merge gate:
- frontend build passes;
- backend result is reported honestly;
- no backend files change;
- Import Apply behavior diff remains copy-only;
- state/progress.md and state/handoff.md are append-only;
- repository owner reviews and approves the focused PR.

No future PR number is assigned.
