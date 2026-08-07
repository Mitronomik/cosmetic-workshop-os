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

```text
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — AUTHORIZED — DECISION ONLY — NOT DECIDED
C4-II-A — PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

The repository intentionally does not embed a permanently changing current
baseline SHA in this README.

For lifecycle and authorization, read in this order:

1. [`docs/current-lifecycle.md`](docs/current-lifecycle.md)
2. [`docs/implementation-plan.md`](docs/implementation-plan.md)
3. [`state/current-focus.md`](state/current-focus.md)
4. [`state/progress.md`](state/progress.md)
5. [`state/handoff.md`](state/handoff.md)
6. [`state/change-requests.md`](state/change-requests.md)

## Current action while PR #171 is open

PR #171 is the current documentation closure gate.

```text
finish independent audit
→ correct every finding
→ run documentation checks in a real checkout
→ repeat exact-head read-only audit
→ merge PR #171
```

Do not start CR-011 from the unmerged PR #171 branch.
Do not create a dependent CR-011 branch from the PR #171 head.

## Authorized successor after PR #171 merges

After PR #171 is merged, update `main` and create a new branch from the merged
`main`. Only then begin:

```text
CR-011 — Decide the launcher Restore interaction and validation-session boundary.
Decision-only. No runtime implementation is authorized.
```

C4-II-A remains planned, blocked by CR-011, and not authorized.

## Lifecycle consistency note

`docs/architecture.md`, `docs/roadmap.md`, `docs/backup-and-restore.md`, and the
dated implementation-status blocks in ADR 0016 retain valuable product,
safety, and architecture context but contain branch-era C4 lifecycle wording.

Current lifecycle and authorization are governed by:

- [`docs/current-lifecycle.md`](docs/current-lifecycle.md);
- ADR 0017;
- the active implementation plan.

ADR 0016 remains authoritative for the launcher-assisted Restore product and
safety decision, including its twelve-phase state machine and recovery contract.
Only its dated implementation-status / authorization wording is superseded by
ADR 0017 after PR #170 merged.

No agent may reopen C4-I or authorize C4-II runtime work from a historical status
sentence.

## C4-I history and current Restore decision

- Current lifecycle authority:
  [`docs/current-lifecycle.md`](docs/current-lifecycle.md)
- Current lifecycle and architecture gate:
  [`docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md`](docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md)
- Normative Restore interaction and non-destructive validation-session profile:
  [`docs/restore-interaction-and-validation-session.md`](docs/restore-interaction-and-validation-session.md)
- Accepted launcher-assisted Restore safety contract:
  [`docs/decisions/0016-launcher-assisted-restore.md`](docs/decisions/0016-launcher-assisted-restore.md)
- C4-I implementation and six-round audit history:
  [`docs/history/c4-i-implementation-and-audit-history.md`](docs/history/c4-i-implementation-and-audit-history.md)
- Project timeline and exact pre-compaction snapshots:
  [`docs/history/README.md`](docs/history/README.md)
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
- [`docs/current-lifecycle.md`](docs/current-lifecycle.md) — lifecycle authority
  and supersession map
- [`docs/product-spec.md`](docs/product-spec.md) — product specification
- [`docs/architecture.md`](docs/architecture.md) — architecture contract
- [`docs/restore-interaction-and-validation-session.md`](docs/restore-interaction-and-validation-session.md)
  — current C4 interaction/validation-session profile
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
- [`state/change-requests.md`](state/change-requests.md) — compact current CR ledger
- [`docs/history/README.md`](docs/history/README.md) — searchable history index

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

## Restore boundary until CR-011 is accepted

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

The later CR-011 decision must select one concrete interaction architecture and
define the launcher-owned non-destructive validation-session boundary before
C4-II-A can be authorized.

## Documentation check

After lifecycle documentation changes, run:

```bash
python3 scripts/check_documentation_lifecycle.py
```

This is a documentation consistency check, not product smoke.