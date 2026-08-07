# Progress

Updated: `2026-08-07`

Current lifecycle authority: `docs/current-lifecycle.md`.

## Completed / merged baseline

- C1 — completed.
- C2 — completed.
- C3 — completed, merged, exact-head verified and hardened.
- CR-010 — launcher-assisted Restore semantics accepted.
- C4-I — launcher-owned Restore safety engine: `DONE — MERGED AND EXACT-HEAD VERIFIED`.
- PR #170 reviewed head: `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8`.
- PR #170 merge commit: `e6997281d2e0268ce54184d988c114bac71c35e2`.
- Six independent C4-I audit rounds closed twenty-four findings.
- PR #171 — project-memory/lifecycle closure — merged.
- PR #171 reviewed head: `4978aa9a7c05117011eae1bc00276d5f98378d9b`.
- PR #171 merge commit: `76ab59216047222714a32f2793a789b3dc8df19a`.
- PR #172 / CR-011 interaction decision — merged.
- PR #172 reviewed head: `c51d5baa07e4cd8912b1973649c22b20f581e3d2`.
- PR #172 merge commit: `998596560db6780a677bdec363d1fd19db30c1b6`.
- PR #172 exact-head architecture audit: P0=0, P1=0, P2=0.
- Searchable history and five exact pre-compaction snapshots remain protected under `docs/history/`.

## Current lifecycle

```text
PR #172 — MERGED — CR-011 ACCEPTED
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

The sliced authorization becomes normative only when PR #173 merges to `main`.

## Current work — PR #173

PR #173 is documentation/lifecycle only.

Its job is to:

- record PR #172 as merged / CR-011 accepted;
- authorize C4-II-A only as A1→A4 bounded implementation slices;
- make A1 the only immediate runtime successor;
- keep A2/A3/A4 predecessor-gated;
- keep C4-II-B not authorized;
- synchronize active lifecycle/status surfaces and checker.

No runtime or tests belong in this branch.

## Authorized implementation sequence after PR #173 merge

### A1 — Validation-session core — next

Launcher-owned non-destructive candidate preparation, C4-I primitive reuse,
validation scratch, generation/cancel/stale semantics, typed safe result,
retained `SourceIdentity` + SHA-256 proof, owned-only cleanup, tests and
service-level smoke.

### A2 — Exact-run control plane — blocked by A1 merge

Loopback Host/Origin/bootstrap/session/concurrency/replay/command ordering only.
No real picker or final UI.

### A3 — Native picker integration — blocked by A2 merge

Real `/usr/bin/osascript` + Standard Additions `choose file`, picker worker
lifecycle and A1 integration. No final browser workspace.

### A4 — Browser Restore screen — blocked by A3 merge

`/backups/restore`, entry from `/backups`, fragment/sessionStorage handling,
typed safe UX and real non-destructive end-to-end macOS smoke.

## Cross-slice prohibition

No A1–A4 slice may call `execute_restore(...)`, create a durable Restore
operation/phase, create `before_restore` safety copy, replace/migrate working DB,
perform rollback/recovery mutation or write Restore AuditLog.

C4-II-B remains separately not authorized.

## Open product obligations

- validate/audit/merge PR #173;
- implement/review/merge A1;
- then A2;
- then A3;
- then A4 + exact-head non-destructive end-to-end smoke;
- separately authorize and implement C4-II-B;
- C4-II-C outcome/restart/support UX;
- C4-III end-to-end Restore verification;
- macOS packaging;
- safe packaged update flow;
- installation verification;
- full release-candidate smoke.

## Required checks for PR #173

```bash
git diff --check
python3 scripts/check_documentation_lifecycle.py
```

Also verify docs/state/checker-only diff and run repository-defined Markdown/link
check if present. Product smoke: **NOT APPLICABLE** for this docs-only changeset.
