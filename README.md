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
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — DECIDED — ADR 0018 ACCEPTED — NORMATIVE ON MAIN
C4-II-A — PLANNED — NOT AUTHORIZED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

On a CR-011 pull-request branch, ADR 0018 is not project authority until that
changeset is merged to `main`. C4-II-A is not authorized by this decision PR.

For current lifecycle/authorization read:

1. [`docs/current-lifecycle.md`](docs/current-lifecycle.md)
2. newest applicable ADR
3. [`docs/implementation-plan.md`](docs/implementation-plan.md)
4. [`state/current-focus.md`](state/current-focus.md)
5. [`state/progress.md`](state/progress.md)
6. [`state/handoff.md`](state/handoff.md)
7. [`state/change-requests.md`](state/change-requests.md)

## CR-011 decision

ADR 0018 selects one concrete interaction architecture:

```text
ordinary browser presentation
→ launcher-owned HTTP control plane on 127.0.0.1:<ephemeral>
→ launcher-owned native macOS picker
→ launcher-owned non-destructive validation session
→ existing C4-I intake/staging/validation semantics
```

Key decisions:

- control plane is separate from ordinary FastAPI business API;
- exact configured local frontend Origin only; no wildcard CORS;
- one-use 256-bit bootstrap capability enters through URL fragment;
- run-scoped browser token lives only in `sessionStorage`;
- absolute selected-source path never enters browser/ordinary backend state;
- native picker is an owned `/usr/bin/osascript` child using Standard Additions
  `choose file`;
- no new application dependency is authorized;
- ordinary backend remains running during non-destructive validation;
- candidate preparation must reuse C4-I held-descriptor, sidecar, two-pass digest
  staging and read-only candidate validation semantics;
- future C4-II-B must reopen/re-prove source identity + SHA-256, restage and
  revalidate before destructive Restore.

Normative decision:

- [`docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`](docs/decisions/0018-launcher-restore-interaction-and-validation-session.md)

Normative working profile:

- [`docs/restore-interaction-and-validation-session.md`](docs/restore-interaction-and-validation-session.md)

## Current action

This CR-011 changeset is documentation/architecture only.

Before merge:

```text
finish documentation synchronization
→ git diff --check
→ python3 scripts/check_documentation_lifecycle.py
→ run repository-defined docs/link checker if present
→ verify no backend/frontend/launcher runtime path changed
→ fresh independent exact-head architecture audit
→ resolve every P0/P1/P2 finding
→ merge CR-011 decision PR
```

Do not implement C4-II-A on this branch.

After CR-011 is merged to `main`, prepare a separate bounded task that explicitly
authorizes C4-II-A. Do not treat ADR acceptance as implicit runtime authorization.

## Restore authority

Authority is intentionally split:

- ADR 0016 — durable launcher-assisted Restore safety/state machine;
- ADR 0017 — C4-I lifecycle closure and CR-011 gate;
- ADR 0018 — interaction/control/picker/validation-session architecture;
- `docs/current-lifecycle.md` — current implementation authorization.

ADR 0018 does not change the twelve phases, transition graph, startup recovery
matrix, `replacement_intent`, mandatory safety-copy rule, immutable-source rule,
or Restore AuditLog boundary accepted by ADR 0016.

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