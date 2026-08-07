# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop: recipes and versions,
individual client formulas, clients/feedback, ingredients/lots, packaging,
orders, production, stock movements, alerts, purchases, imports, exports,
backups, onboarding and help.

The product goal is a packaged local application that a non-technical user can
open and use without GitHub, Git, Python, Node.js, Docker or a terminal.

## Current product status

```text
PR #171 — MERGED
PR #172 — MERGED — CR-011 ACCEPTED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — AUTHORIZED AS SLICED — NOT IMPLEMENTED
C4-II-A1 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A2 — PLANNED — BLOCKED BY A1 MERGE + EXACT-HEAD GATE
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

On the PR #173 authorization branch, this C4-II-A authorization becomes project
authority only when the changeset is merged to `main`. No runtime implementation
belongs in PR #173 itself.

For current lifecycle/authorization read:

1. [`docs/current-lifecycle.md`](docs/current-lifecycle.md)
2. newest applicable ADR
3. [`docs/c4-ii-a-implementation-slices.md`](docs/c4-ii-a-implementation-slices.md)
4. [`docs/implementation-plan.md`](docs/implementation-plan.md)
5. [`state/current-focus.md`](state/current-focus.md)
6. [`state/progress.md`](state/progress.md)
7. [`state/handoff.md`](state/handoff.md)
8. [`state/change-requests.md`](state/change-requests.md)

## Restore authority

Authority is intentionally split:

- ADR 0016 — durable launcher-assisted destructive Restore safety/state machine;
- ADR 0017 — C4-I lifecycle closure and CR-011 gate;
- ADR 0018 — interaction/control/picker/validation-session architecture;
- `docs/c4-ii-a-implementation-slices.md` — bounded A1→A4 implementation
  authorization and PR gates;
- `docs/current-lifecycle.md` — current implementation authorization.

ADR 0018 does not change the twelve phases, transition graph, startup recovery
matrix, `replacement_intent`, mandatory safety-copy rule, immutable-source rule,
or Restore AuditLog boundary accepted by ADR 0016.

## C4-II-A implementation sequence

C4-II-A is deliberately split into four small PRs:

```text
A1 — validation-session core
→ A2 — exact-run launcher control plane
→ A3 — native macOS picker integration
→ A4 — browser /backups/restore + end-to-end non-destructive flow
```

Only **A1** is authorized to begin after PR #173 merges. A2–A4 require their
predecessor to be independently reviewed, exact-head tested, merged, and the
lifecycle state updated before the next branch is created.

C4-II-B destructive confirmation/execution remains **NOT AUTHORIZED**.

Complete slice contract:

- [`docs/c4-ii-a-implementation-slices.md`](docs/c4-ii-a-implementation-slices.md)

Selected interaction architecture:

- [`docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`](docs/decisions/0018-launcher-restore-interaction-and-validation-session.md)
- [`docs/restore-interaction-and-validation-session.md`](docs/restore-interaction-and-validation-session.md)

## Current action — PR #173

PR #173 is documentation/lifecycle only.

Before merge:

```text
synchronize post-#172 lifecycle
→ git diff --check
→ python3 scripts/check_documentation_lifecycle.py
→ verify docs/state/checker-only diff
→ fresh independent exact-head documentation/authorization audit
→ resolve every P0/P1/P2 finding
→ merge PR #173
```

Do not implement A1 on the unmerged PR #173 branch.

After PR #173 merges, update `main`, create a fresh A1 branch, and implement only
`C4-II-A1 — Validation-session core`.

## Project history

Searchable history is retained under [`docs/history/`](docs/history/README.md).
Exact pre-compaction snapshots remain byte-identical and are protected by
`scripts/check_documentation_lifecycle.py`.

History is non-normative evidence and cannot authorize current work.

## Documentation map

### Product and architecture

- [`AGENTS.md`](AGENTS.md) — main agent contract
- [`docs/current-lifecycle.md`](docs/current-lifecycle.md) — lifecycle authority
- [`docs/product-spec.md`](docs/product-spec.md) — product specification
- [`docs/architecture.md`](docs/architecture.md) — durable architecture
- [`docs/domain-model.md`](docs/domain-model.md) — domain model
- [`docs/roadmap.md`](docs/roadmap.md) — strategic roadmap
- [`docs/implementation-plan.md`](docs/implementation-plan.md) — active sequence
- [`docs/c4-ii-a-implementation-slices.md`](docs/c4-ii-a-implementation-slices.md)
  — C4-II-A authorization/slicing
- [`docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`](docs/decisions/0018-launcher-restore-interaction-and-validation-session.md)
  — CR-011 decision
- [`docs/restore-interaction-and-validation-session.md`](docs/restore-interaction-and-validation-session.md)
  — Restore interaction profile

### UI/product language

- [`docs/ui-ux-contract.md`](docs/ui-ux-contract.md)
- [`docs/frontend-concept.md`](docs/frontend-concept.md)
- [`docs/user-guide.md`](docs/user-guide.md)

### Data safety/operations

- [`docs/backup-and-restore.md`](docs/backup-and-restore.md)
- [`docs/deployment.md`](docs/deployment.md)
- [`docs/packaging.md`](docs/packaging.md)
- [`docs/local-install.md`](docs/local-install.md)
- [`docs/update-guide.md`](docs/update-guide.md)
- [`docs/pr-testing-and-smoke-rules.md`](docs/pr-testing-and-smoke-rules.md)

### Project memory

- [`docs/codex-project-structure.md`](docs/codex-project-structure.md)
- [`docs/codex-prompting-rules.md`](docs/codex-prompting-rules.md)
- [`state/current-focus.md`](state/current-focus.md)
- [`state/progress.md`](state/progress.md)
- [`state/handoff.md`](state/handoff.md)
- [`state/change-requests.md`](state/change-requests.md)
- [`docs/history/README.md`](docs/history/README.md)

## Architectural invariants

Every change must preserve:

- local-first work without required internet;
- user data separate from code/package;
- deliverable product rather than repository workflow;
- API-first backend business architecture;
- backend-owned business calculations/critical mutations;
- immutable historical production meaning;
- versioned recipes and first-class individual client formulas;
- inventory through lots/movements;
- transactional production;
- import through draft/preview/validation/confirmation/apply;
- backup before migrations;
- understandable non-technical UI;
- no silent MVP expansion into cloud, OCR, full accounting, roles or advanced
  analytics.

Restore additionally preserves launcher ownership of filesystem/destructive
authority and never uses the ordinary browser as absolute-path authority.

## Documentation check

After lifecycle documentation changes run:

```bash
python3 scripts/check_documentation_lifecycle.py
```

This is documentation consistency validation, not product smoke.
