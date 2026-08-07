# Current Focus — CR-011 Restore interaction decision

Updated: `2026-08-07`

Current lifecycle authority: `docs/current-lifecycle.md`.
Current CR-011 decision: `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`.
Current Restore profile: `docs/restore-interaction-and-validation-session.md`.
Current ledger: `state/change-requests.md`.
Searchable history: `docs/history/README.md`.

## Baseline

PR #171 is merged.

```text
PR #171 merge commit — 76ab59216047222714a32f2793a789b3dc8df19a
```

This CR-011 branch was created from that merged `main`.

## Current lifecycle

```text
PR #171 — MERGED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — DECIDED — ADR 0018 ACCEPTED — NORMATIVE ON MAIN
C4-II-A — PLANNED — NOT AUTHORIZED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

On this PR branch, ADR 0018 becomes project authority only after the changeset is
merged to `main`.

## Current task

Finish and validate the **decision-only CR-011 pull request**.

Selected architecture:

```text
ordinary browser presentation
→ exact-run authenticated launcher-owned loopback control plane
→ launcher-owned /usr/bin/osascript native picker
→ launcher-owned non-destructive validation session
→ existing C4-I intake/staging/validation semantics
```

The decision fixes screen/process ownership, picker mechanism, exact-run browser
bootstrap, Origin/CORS rules, path privacy, replay/stale/duplicate protection,
backend lifecycle, scratch cleanup, C4-II-B source re-proof and future exact-head
smoke.

## Allowed scope

- ADR 0018;
- `docs/current-lifecycle.md`;
- `docs/implementation-plan.md`;
- `docs/restore-interaction-and-validation-session.md`;
- bounded deployment/packaging consequences;
- README and active `state/` synchronization;
- `docs/decisions/AGENTS.md` authority synchronization;
- strict documentation lifecycle checker changes.

## Do not touch

No runtime implementation is authorized in this branch.

Do not modify:

- `backend/`;
- `frontend/`;
- `launcher/`;
- runtime tests;
- dependency/lock files;
- migrations;
- workflows;
- packaging implementation;
- updater implementation.

Do not implement:

- native picker;
- launcher control server;
- frontend Restore UI;
- `prepare_restore_candidate(...)` runtime service;
- C4-II-B confirmation/execution;
- C4-II-C/C4-III.

## Selected security boundary

Future C4-II-A, when separately authorized, must preserve:

- control bind `127.0.0.1` + ephemeral port;
- exact configured local frontend Origin only;
- no wildcard CORS;
- one-use >=256-bit bootstrap token in URL fragment;
- fragment removed after bootstrap;
- second >=256-bit run-scoped session token in `sessionStorage` only;
- no durable/reusable token;
- 15s heartbeat / 60s inactive control-session expiry;
- request replay/idempotency ledger;
- selection-generation stale-result protection;
- browser never receives authoritative absolute source path.

## Validation boundary

Future candidate preparation is non-destructive and launcher-owned.

It must reuse C4-I source intake, sidecar checks, held-descriptor identity/digest,
two-pass stable staging and read-only candidate validation. It creates no durable
Restore operation, phase, safety copy, working-DB mutation or Restore AuditLog
event.

After successful validation, temporary staged scratch is deleted. Launcher memory
retains source path + `SourceIdentity` + SHA-256 proof. Future C4-II-B must reopen,
re-prove, restage and revalidate before destructive execution.

## Required checks before merge

```bash
git diff --check
python3 scripts/check_documentation_lifecycle.py
```

Also:

- run a project-defined Markdown/link checker if one exists;
- verify no `backend/`, `frontend/` or `launcher/` path changed;
- perform fresh independent exact-head read-only architecture audit;
- resolve every P0/P1/P2 finding.

Product smoke is not applicable because this is a documentation/architecture
changeset only.

## After this PR merges

Do **not** begin C4-II-A by assumption.

Create a separate bounded task/PR that explicitly authorizes C4-II-A against the
merged ADR 0018 architecture.