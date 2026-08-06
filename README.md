# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop: recipes and recipe
versions, individual client formulas, clients and feedback, ingredients and
lots, packaging, orders, production, stock movements, alerts, purchase
suggestions, imports, exports, backups, onboarding, and help.

The product goal is a packaged local application that a non-technical user can
open, understand, update, and use without GitHub, Git, Python, Node.js, Docker,
or a terminal.

## Current product status

- C1 — completed.
- C2 — completed.
- C3 — completed, merged, exact-head verified, and hardened.
- CR-010 — launcher-assisted Restore semantics accepted.
- C4-I — launcher-owned Restore safety infrastructure merged and exact-head
  verified in PR #170.
- User-facing Restore — **not implemented**.
- Product release readiness — **not claimed**.

The repository intentionally does not embed a permanently changing current
baseline SHA in this README.

For the current implementation state and next authorized task, read:

1. [`docs/implementation-plan.md`](docs/implementation-plan.md)
2. [`state/current-focus.md`](state/current-focus.md)
3. [`state/progress.md`](state/progress.md)
4. [`state/handoff.md`](state/handoff.md)

The only authorized next task is the decision-only CR-011:

```text
CR-011 — Decide the launcher Restore interaction and validation-session boundary.
Decision-only. No runtime implementation is authorized.
```

C4-II-A remains planned, blocked by CR-011, and not authorized.

## C4-I history and current Restore decision

- Current lifecycle and architecture gate:
  [`docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md`](docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md)
- Normative Restore interaction and non-destructive validation-session profile:
  [`docs/restore-interaction-and-validation-session.md`](docs/restore-interaction-and-validation-session.md)
- Accepted launcher-assisted Restore safety contract:
  [`docs/decisions/0016-launcher-assisted-restore.md`](docs/decisions/0016-launcher-assisted-restore.md)
- Concise implementation and six-round audit history:
  [`docs/history/c4-i-implementation-and-audit-history.md`](docs/history/c4-i-implementation-and-audit-history.md)
- Backup and Restore product/safety contract:
  [`docs/backup-and-restore.md`](docs/backup-and-restore.md)

C4-I is internal safety infrastructure. It does not provide a user-facing file
picker, validation screen, destructive confirmation, Restore action, terminal
outcome screen, ordinary FastAPI Restore endpoint, or ordinary SPA Restore
mutation.

The launcher currently opens an ordinary system browser. There is not yet an
accepted browser-to-launcher command channel or a public non-destructive
validation-session service. CR-011 must choose those boundaries before runtime
work begins.

## Documentation map

### Product and architecture

- [`AGENTS.md`](AGENTS.md) — main Codex contract
- [`docs/product-spec.md`](docs/product-spec.md) — product specification
- [`docs/architecture.md`](docs/architecture.md) — architecture contract
- [`docs/restore-interaction-and-validation-session.md`](docs/restore-interaction-and-validation-session.md)
  — current normative C4 interaction/validation-session profile
- [`docs/domain-model.md`](docs/domain-model.md) — domain model
- [`docs/roadmap.md`](docs/roadmap.md) — strategic roadmap
- [`docs/implementation-plan.md`](docs/implementation-plan.md) — active
  implementation sequence and release gates

### UI and product language

- [`docs/ui-ux-contract.md`](docs/ui-ux-contract.md) — human-friendly UI rules
- [`docs/frontend-concept.md`](docs/frontend-concept.md) — frontend concept
- [`docs/user-guide.md`](docs/user-guide.md) — user guidance

### Data safety and operations

- [`docs/backup-and-restore.md`](docs/backup-and-restore.md) — backup and Restore
  contract
- [`docs/local-install.md`](docs/local-install.md) — local installation
- [`docs/update-guide.md`](docs/update-guide.md) — safe update contract
- [`docs/pr-testing-and-smoke-rules.md`](docs/pr-testing-and-smoke-rules.md) — PR
  test and smoke requirements
- [`docs/smoke-script-authoring-rules.md`](docs/smoke-script-authoring-rules.md) —
  external smoke-runner rules

### Development memory

- [`docs/codex-project-structure.md`](docs/codex-project-structure.md) — project
  memory structure
- [`docs/codex-prompting-rules.md`](docs/codex-prompting-rules.md) — Codex task
  rules
- [`state/current-focus.md`](state/current-focus.md) — current task
- [`state/progress.md`](state/progress.md) — current progress
- [`state/handoff.md`](state/handoff.md) — cross-session handoff
- [`docs/history/`](docs/history/) — curated non-authoritative historical records

## Architectural invariants

Every change must preserve:

- local-first work without required internet;
- user data stored separately from application code and package contents;
- a deliverable product rather than a repository-based user workflow;
- API-first backend architecture;
- backend-owned business calculations and critical mutations;
- immutable historical production data;
- versioned recipes and first-class individual client formulas;
- inventory through lots and movements;
- transactional production;
- import through draft, preview, validation, confirmation, and apply;
- backup before migration;
- understandable non-technical UI and error language;
- no silent expansion into cloud sync, OCR, full accounting, roles,
  multi-user operation, or advanced analytics in the MVP.

## Restore boundary until CR-011

No agent may add, by assumption:

- a FastAPI Restore endpoint;
- SPA-owned filesystem access;
- browser upload as the authoritative Restore source;
- a generic unauthenticated localhost endpoint;
- wildcard CORS;
- an undocumented WebSocket or IPC channel;
- a native shell technology or dependency not selected by an accepted decision;
- an absolute selected-source path in ordinary browser state;
- hidden Restore packaging work.

The next accepted decision must select one concrete interaction architecture and
define the launcher-owned non-destructive validation-session boundary before
C4-II-A can be authorized.