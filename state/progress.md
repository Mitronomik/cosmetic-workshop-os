# Progress

Updated: `2026-08-07`

Current lifecycle authority: `docs/current-lifecycle.md`.

## Completed / merged baseline

- C1 — completed.
- C2 — completed.
- C3 — completed, merged, exact-head verified and hardened.
- CR-010 — launcher-assisted Restore semantics accepted.
- C4-I — launcher-owned Restore safety engine:
  `DONE — MERGED AND EXACT-HEAD VERIFIED`.
- PR #170 reviewed head:
  `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8`.
- PR #170 merge commit:
  `e6997281d2e0268ce54184d988c114bac71c35e2`.
- Six independent C4-I audit rounds closed twenty-four findings.
- PR #171 — project-memory/lifecycle closure — merged.
- PR #171 reviewed head:
  `4978aa9a7c05117011eae1bc00276d5f98378d9b`.
- PR #171 merge commit:
  `76ab59216047222714a32f2793a789b3dc8df19a`.
- Searchable history and five exact pre-compaction snapshots remain protected
  under `docs/history/`.

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

On the CR-011 PR branch, ADR 0018 becomes normative only after merge to `main`.

## CR-011 decision produced

The current decision changeset selects **one** interaction architecture:

```text
ordinary browser
→ launcher-owned authenticated loopback control plane
→ launcher-owned native macOS picker
→ launcher-owned non-destructive validation session
→ C4-I source intake/staging/validation
```

ADR:

`docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`

Normative profile:

`docs/restore-interaction-and-validation-session.md`

### Security/process decision

- `127.0.0.1` only;
- OS-assigned ephemeral control port;
- separate from ordinary FastAPI business API;
- exact local frontend Origin, no wildcard CORS;
- one-use >=256-bit bootstrap token in URL fragment;
- >=256-bit run-scoped browser session token in `sessionStorage` only;
- 15-second heartbeat / 60-second inactive control-session expiry;
- replay/idempotency request IDs;
- monotonically increasing selection generation;
- no WebSocket;
- no generic launcher command surface;
- no durable token;
- absolute selected-source path remains launcher-private.

### Picker decision

- launcher owns picker authority;
- owned short-lived `/usr/bin/osascript` child;
- macOS Standard Additions `choose file`;
- no `shell=True`;
- no `System Events`;
- no new Python/application dependency;
- Mac App Store sandbox support deferred to a later packaging decision.

### Validation decision

Future C4-II-A must implement a launcher-owned
`prepare_restore_candidate(...)`-equivalent that:

- creates no durable Restore operation;
- enters no Restore phase;
- creates no `before_restore` safety copy;
- changes no working database;
- writes no Restore AuditLog event;
- reuses C4-I source intake, held descriptor, sidecar checks, digest-stable
  staging and candidate validation;
- uses isolated temporary scratch;
- returns typed safe presentation only.

After successful validation the temporary staged candidate is deleted. Launcher
memory retains the source path + C4-I `SourceIdentity` + full SHA-256 proof.

Future C4-II-B must reopen, compare identity, recompute digest, re-check sidecars,
restage and revalidate before entering destructive C4-I execution.

## Current work

Finish the CR-011 decision PR only:

```text
synchronize docs/state/checker
→ run documentation checks in real checkout
→ verify docs-only diff
→ fresh independent exact-head architecture audit
→ correct every P0/P1/P2 finding
→ merge CR-011 decision PR
```

No runtime work belongs in this branch.

## Planned but not authorized

```text
C4-II-A — PLANNED — NOT AUTHORIZED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
```

CR-011 removes the architecture ambiguity; it does not itself authorize C4-II-A.

## Open product obligations

- separate bounded C4-II-A authorization/task after CR-011 merge;
- C4-II-A source selection + non-destructive validation presentation;
- C4-II-B destructive confirmation/execution handoff;
- C4-II-C outcome/restart/support UX;
- C4-III end-to-end Restore verification;
- macOS packaging;
- safe packaged update flow;
- installation verification;
- full release-candidate smoke.

## Required checks for current decision PR

```bash
git diff --check
python3 scripts/check_documentation_lifecycle.py
```

Also run a repository-defined Markdown/link check if present and verify no
`backend/`, `frontend/` or `launcher/` path changed.

Product smoke: **NOT APPLICABLE** for this documentation/architecture changeset.