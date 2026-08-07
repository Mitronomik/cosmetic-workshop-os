# cosmetic-workshop-os — Active implementation plan

Project: `cosmetic-workshop-os`  
Client-facing name: **Мастерская косметолога**  
Document: `docs/implementation-plan.md`  
Status: **active current implementation sequence**  
Updated: `2026-08-07`

The complete pre-compaction implementation plan is preserved byte-for-byte in
the current repository tree:

[`docs/history/implementation-plan/2026-08-06-pre-compaction.md`](history/implementation-plan/2026-08-06-pre-compaction.md)

The same source is also recoverable from the PR #170 merge baseline:

```bash
git show e6997281d2e0268ce54184d988c114bac71c35e2:docs/implementation-plan.md
```

The snapshot contains valuable slice contracts, evidence, known limitations, and
branch-era lifecycle statements. It is historical and must not be used as current
implementation authorization. The searchable C4-I history is retained separately
in `docs/history/c4-i-implementation-and-audit-history.md`, and the broader
project timeline is `docs/history/project-timeline-through-pr170.md`.

## 1. Purpose

This document manages the current bounded implementation window and the next
release gates. It does not replace the strategic roadmap or architecture
contract.

Use it together with:

- `AGENTS.md` and nested `AGENTS.md` files;
- `docs/current-lifecycle.md`;
- `docs/architecture.md`;
- `docs/product-spec.md`;
- `docs/domain-model.md`;
- `docs/roadmap.md`;
- `docs/backup-and-restore.md`;
- `docs/decisions/0016-launcher-assisted-restore.md`;
- `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md`;
- `docs/restore-interaction-and-validation-session.md`;
- `docs/pr-testing-and-smoke-rules.md`;
- `state/current-focus.md`;
- `state/progress.md`;
- `state/handoff.md`;
- `state/change-requests.md`.

## 2. Source-of-truth order

Use `docs/current-lifecycle.md` for the exact current lifecycle, authorization,
and PR sequencing.

For ADR conflicts, apply scope and recency:

1. applicable `AGENTS.md` files;
2. the newest accepted ADR that explicitly supersedes or amends the exact topic;
3. `docs/current-lifecycle.md` for current lifecycle and authorization;
4. older accepted ADRs for durable product/safety/architecture semantics that
   have not been superseded;
5. current normative architecture/profile documents;
6. product/domain documents;
7. strategic roadmap;
8. this implementation plan;
9. active `state/` files.

For Restore, ADR 0017 supersedes only dated C4 lifecycle/status wording in ADR
0016. ADR 0016 remains authoritative for the accepted launcher-assisted Restore
product and safety contract, twelve phases, transition graph, recovery matrix,
`replacement_intent`, launcher ownership, immutable source, safety-copy rule,
and AuditLog boundary.

`docs/architecture.md`, `docs/roadmap.md`, `docs/backup-and-restore.md`, and the
dated implementation-status blocks in ADR 0016 retain valuable context but may
contain pre-merge lifecycle labels. Those labels do not reopen C4-I or authorize
C4-II runtime work.

Historical files under `docs/history/` are evidence and context only. They never
override an active lifecycle or accepted newer decision.

## 3. Current baseline and lifecycle

PR #170 — `C4-I — Implement launcher-owned Restore safety engine` — is merged.

| Item | Verified value |
|---|---|
| Final independently reviewed and exact-head-tested implementation head | `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8` |
| Merge commit on `main` | `e6997281d2e0268ce54184d988c114bac71c35e2` |
| Merged at | `2026-08-03T16:12:23Z` |
| Merge relationship | reviewed head is a parent of the merge commit |
| Additional file changes introduced by merge commit | none |

Accepted PR #170 evidence, not re-executed by PR #171:

- full backend + launcher suite: `2398 passed`;
- launcher suite: `531 passed`;
- frontend `test:*` scripts: `21 / 21 passed`;
- frontend production build: `PASS`;
- ordinary launcher/product regression gate: `11 / 11 PASS`;
- PR-specific Restore smoke: `28 / 28 PASS`;
- final independent merge gate: no P0, P1, or P2 findings.

Detailed evidence and all six audit rounds are retained in:

[`docs/history/c4-i-implementation-and-audit-history.md`](history/c4-i-implementation-and-audit-history.md)

```text
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED

CR-011 — Launcher Restore interaction and validation-session boundary
— AUTHORIZED — DECISION ONLY — NOT DECIDED

C4-II-A — Launcher Restore source selection and validation presentation
— PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED

Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
installation verification — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

## 4. Current implementation window — close PR #171

While PR #171 is open and unmerged, the only active task is the documentation
closure gate itself:

```text
finish independent documentation/architecture audit
→ correct every finding
→ run required documentation checks in a real checkout
→ repeat exact-head read-only audit
→ merge PR #171
```

Do not start CR-011 from the unmerged PR #171 branch.
Do not create a dependent CR-011 branch from the PR #171 head.
Do not add runtime work to PR #171.

Required PR #171 checks:

- `git diff --check`;
- `python3 scripts/check_documentation_lifecycle.py`;
- Markdown/link check if the repository defines one;
- verify only documentation/state/documentation-check paths changed;
- independent exact-head read-only documentation and architecture audit.

Product smoke is not applicable because PR #171 changes no product runtime
behavior.

## 5. Authorized successor after PR #171 merges

After PR #171 merges, update local `main` and create a new branch from that merged
`main`. Only then begin:

```text
CR-011 — Decide the launcher Restore interaction and validation-session boundary.
Decision-only. No runtime implementation is authorized.
```

CR-011 must produce one accepted architecture decision. It must not implement the
chosen architecture.

The decision must select one concrete solution and define:

1. where the user-facing C4-II-A screen lives;
2. which process owns that screen;
3. which process opens the native macOS file picker;
4. how a browser action, if any, reaches the launcher;
5. whether an absolute source path leaves launcher-owned state;
6. whether the ordinary backend remains running during selection and validation;
7. how the channel is bound to the exact local launcher run;
8. origin, token, replay, stale-session, and duplicate-action protection;
9. allowed dependencies;
10. packaging changes required or explicitly deferred;
11. the non-technical packaged user entry path;
12. cancellation, reselection, launcher-exit, and interrupted-session cleanup;
13. isolated exact-head smoke for the chosen boundary.

The decision may compare a launcher-native pre-start flow and a narrowly
authenticated launcher-owned loopback control plane. It must not leave multiple
incompatible architectures equally authorized.

### Explicitly not authorized before CR-011 is accepted

No agent may implement:

- C4-II-A, C4-II-B, C4-II-C, or C4-III;
- a native picker;
- launcher IPC or WebSocket communication;
- a loopback control service;
- a FastAPI Restore endpoint;
- SPA-owned filesystem access;
- browser upload or blob transfer as the authoritative Restore source;
- frontend Restore controls;
- a validation-session Python service;
- Restore packaging changes;
- destructive Restore execution.

## 6. Why C4-II-A is blocked

The current launcher opens an ordinary system browser through
`webbrowser.open(...)`.

The ordinary browser page cannot call a launcher-owned native picker without a
separately designed command channel. It also cannot receive an authoritative
absolute local path from `<input type="file">`; using selected bytes would be a
browser-upload/blob architecture, which is not currently authorized.

The current public C4-I package exposes destructive execution and startup
recovery entry points. It does not expose a dedicated public non-destructive
candidate-preparation session.

Therefore C4-II-A would otherwise have to invent both:

- the browser/application-shell-to-launcher interaction boundary; and
- the non-destructive validation-session application boundary.

Those are architecture and security decisions and must be resolved by CR-011.

## 7. Mandatory future validation-session contract

The complete normative profile is:

[`docs/restore-interaction-and-validation-session.md`](restore-interaction-and-validation-session.md)

Future C4-II-A must use one launcher-owned application boundary conceptually
represented as:

```text
prepare_restore_candidate(...)
```

The eventual code name is not fixed. The semantic contract is mandatory.

The future boundary must:

- never call `execute_restore(...)`;
- create no durable Restore operation record;
- enter none of the twelve Restore phases;
- create no `before_restore` safety copy;
- replace no working database;
- migrate no working database;
- perform no rollback or startup-recovery mutation;
- write no Restore AuditLog event;
- leave the selected source byte-identical;
- use isolated temporary staging distinct from a durable Restore operation
  workspace;
- reuse accepted C4-I source intake, staging, stability, and validation rules;
- return typed presentation results;
- keep raw technical detail in local logs;
- use opaque launcher-owned session identity;
- reject stale results;
- invalidate old results on cancellation and reselection;
- protect duplicate actions;
- clean owned temporary state after cancellation, reselection, failure, and
  launcher shutdown;
- provide bounded cleanup recovery after interruption;
- give the browser no authority over the selected-source path;
- forbid compatibility inference from filename or extension;
- never claim that Restore completed.

An opaque token is a reference to launcher-owned state, not proof that the source
remains valid.

Future C4-II-B must re-prove the immutable source or explicitly retained candidate
identity through launcher-owned state and accepted C4-I safety rules before
destructive execution.

## 8. Preserved architecture constraints

Every future slice must preserve:

- local-first operation without required internet;
- user data stored separately from application code and package contents;
- product delivery without GitHub, Git, Python, Node.js, Docker, or terminal use;
- API-first backend architecture;
- backend-owned calculations and critical mutations;
- immutable historical production data;
- versioned recipes and first-class individual client formulas;
- lot- and movement-based inventory;
- transactional production;
- import through draft, preview, validation, confirmation, and apply;
- backup before migration;
- understandable non-technical UI and error language;
- no cloud sync, OCR, full accounting, roles, multi-user operation, or advanced
  analytics added to the MVP without a separate decision.

Restore-specific invariants remain:

- launcher ownership of destructive Restore;
- immutable selected source;
- complete staging and validation before destructive mutation;
- mandatory verified `before_restore` safety copy before replacement;
- exactly twelve durable phases;
- `phase` as the sole authoritative lifecycle field;
- accepted transition graph and startup recovery matrix unchanged;
- conservative `replacement_intent` recovery;
- no ordinary FastAPI Restore mutation;
- no ordinary SPA filesystem replacement or locking;
- no Restore AuditLog event;
- `rolled_back` is failed Restore;
- `recovery_blocked` blocks ordinary startup;
- ordinary browser opening only after durable `completed`.

## 9. Required shape of the CR-011 pull request

The CR-011 task must be a small decision-only pull request created **after PR
#171 has merged and from updated `main`**.

### Scope

- inspect current launcher, browser, packaging, and C4-I entry boundaries;
- compare bounded interaction alternatives;
- select one architecture;
- define the security and process-lifecycle contract;
- define the non-destructive validation-session ownership contract;
- update architecture and Restore documentation;
- define future C4-II-A tests and exact-head smoke boundary.

### Non-goals

- no runtime code;
- no frontend code;
- no backend code;
- no launcher code;
- no dependency change;
- no packaging implementation;
- no state-machine change;
- no C4-II-A authorization unless the decision is complete, internally
  consistent, and independently audited.

### Tests and checks

- `git diff --check`;
- `python3 scripts/check_documentation_lifecycle.py` if lifecycle docs change;
- Markdown/link check if defined;
- search for conflicting active lifecycle statements;
- verify only documentation/state paths changed;
- independent read-only architecture audit.

## 10. Release gates after CR-011

CR-011 acceptance alone does not implement Restore.

A later documentation closure may authorize C4-II-A only after the interaction
and validation-session boundaries are unambiguous.

C4-II-B remains blocked until C4-II-A is implemented, independently reviewed,
exact-head verified, merged, and closed.

C4-II-C remains blocked until the execution result vocabulary and restart handoff
are implemented and reviewed.

C4-III remains the end-to-end product verification and lifecycle closure gate.
It is not a place to hide broad runtime implementation.

Packaging, safe packaged updates, installation verification, and full
release-candidate smoke remain separate open obligations.

## 11. Current next action

```text
Close PR #171 safely.
Do not begin CR-011 until PR #171 is merged and a new branch is created from
updated main.
```