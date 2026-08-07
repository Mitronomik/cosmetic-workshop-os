# Handoff

Updated: `2026-08-07`

Current lifecycle authority: `docs/current-lifecycle.md`.
Current CR-011 decision: `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`.
Current Restore profile: `docs/restore-interaction-and-validation-session.md`.
Current ledger: `state/change-requests.md`.
Searchable history: `docs/history/README.md`.

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

On the decision PR branch, ADR 0018 becomes project authority only after merge to
`main`.

## Last merged work

PR #171 merged from reviewed head:

`4978aa9a7c05117011eae1bc00276d5f98378d9b`

into merge commit:

`76ab59216047222714a32f2793a789b3dc8df19a`

It preserved project memory/history and established CR-011 as the next
decision-only task.

## Current work — CR-011

CR-011 is now decided in ADR 0018.

Selected architecture:

```text
ordinary browser presentation
→ launcher-owned HTTP control plane on 127.0.0.1:<ephemeral>
→ launcher-owned /usr/bin/osascript picker
→ launcher-owned non-destructive candidate preparation
→ existing C4-I intake/staging/validation semantics
```

Alternative rejected: launcher-native pre-start Restore flow, because the project
has no native shell/navigation surface and introducing one now would make Restore
an early packaging/native-shell redesign.

## Exact-run browser control contract

Future C4-II-A, if separately authorized, must use:

- exact `127.0.0.1` loopback bind;
- OS-assigned ephemeral control port;
- one exact local frontend Origin;
- no wildcard CORS;
- one-use >=256-bit bootstrap token delivered in URL fragment;
- immediate fragment removal after bootstrap;
- second >=256-bit run-scoped token stored only in browser `sessionStorage`;
- no durable token/cookie authority;
- authenticated heartbeat every 15 seconds;
- control session expiry after 60 seconds without authenticated activity;
- per-run replay/idempotency request ledger;
- selection generation that invalidates stale results;
- no destructive control endpoint in C4-II-A.

## Native picker contract

Launcher owns the action.

Future implementation uses an owned short-lived `/usr/bin/osascript` child and
macOS Standard Additions `choose file`.

No `shell=True`, no `System Events`, no absolute path returned to browser/backend,
and no new application dependency.

Mac App Store sandbox compatibility is not claimed and may require a later picker
adapter decision without changing launcher path ownership.

## Candidate validation contract

Future C4-II-A must use a launcher-owned non-destructive boundary conceptually
`prepare_restore_candidate(...)`.

It must reuse existing C4-I:

- `open_selected_source(...)`;
- `HeldSource` identity/revalidation/full digest semantics;
- stable two-pass staging semantics;
- sidecar/self-containment checks;
- `validate_staged_candidate(...)` read-only candidate validation.

It must create no durable Restore operation, phase, safety copy, working-DB
mutation or Restore AuditLog event.

Temporary staged validation candidate is deleted after validation. Launcher
memory retains only private source path + C4-I `SourceIdentity` + SHA-256 proof +
current generation/compatibility.

Future C4-II-B must reopen/re-prove identity and digest, re-check sidecars,
restage and revalidate before destructive C4-I execution.

## Backend lifecycle

Ordinary backend remains running during selection, staging, validation and result
presentation because C4-II-A is non-destructive and operates on an isolated copy.

Backend exclusion/stop proof remains a C4-I/C4-II-B destructive boundary.

## Current branch restrictions

This CR-011 PR is documentation/architecture only.

Do not modify or implement:

- backend/frontend/launcher runtime or tests;
- native picker code;
- control plane code;
- frontend Restore UI;
- validation-session runtime service;
- C4-II-B/C4-II-C/C4-III;
- dependencies, migrations, workflows or packaging implementation.

## Checks before merge

```bash
git diff --check
python3 scripts/check_documentation_lifecycle.py
```

Also:

- run repository-defined docs/link checker if present;
- verify no `backend/`, `frontend/` or `launcher/` path changed;
- fresh independent read-only architecture audit at exact published head;
- P0=0, P1=0, P2=0 before merge.

Product smoke is not applicable for this decision-only changeset.

## Next after CR-011 merge

Do **not** implement C4-II-A automatically.

Create a separate bounded authorization/task from updated `main` that explicitly
scopes C4-II-A against merged ADR 0018. C4-II-B remains separately not
authorized.