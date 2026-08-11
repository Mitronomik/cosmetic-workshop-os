# Progress

Updated: `2026-08-09`

## Completed / merged baseline

- C1/C2 completed; C3 completed, merged, exact-head verified and hardened.
- C4-I — `DONE — MERGED AND EXACT-HEAD VERIFIED`.
- A1/A2/A3/A4 — merged and exact-head verified.
- PR #181 merged as `beae1407af270ad1c800c308ea7907750430eb1d`, closing C4-II-A and authorizing B1.
- PR #182 reviewed `27726058af4f373ab65225ecf4d1a945f1c53067`, merged as `5e13b50f1918dacbf8d54066c9156942a9adb895`; B1 exact-head verified and closed.
- PR #183 reviewed `fa922f56c19a2dd33b6307ae0a197d476f91489b`, merged as `4617b8c436eaa510fd545d863346595e2d808ea7`; B2 only authorized.
- Searchable history and five exact pre-compaction snapshots remain protected.

## Current lifecycle

```text
PR #183 — MERGED — B2 AUTHORIZED
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## B1 final evidence

- focused B1: 10/10;
- Restore privacy: 10/10;
- full backend+launcher: 2480/2480;
- external exact-head source substitution smoke: PASS;
- source changed before `prepared`, no operation record/safety copy/working DB mutation;
- exact repository status/head remained clean;
- independent audit: `P0=0/P1=0/P2=0`.

## B2 implementation changeset

Implemented under the PR #183 authorization:

- exact authenticated `/v1/restore/execute` request with `request_id + command_seq + generation` only;
- ADR 0018 replay semantics and valid-business-refusal sequence consumption;
- one-shot current A1 path/proof transfer into launcher-private in-memory `RestoreExecutionIntent`;
- immediate retained-authority invalidation;
- pathless `restoring`, `restore_completed`, `restore_failed`, `restore_blocked` control states;
- restoring-time select/cancel/second-execute refusal without destructive cancellation;
- browser-session expiry no longer cancels accepted destructive execution;
- main launcher runtime owner loop is the sole intent consumer;
- existing C4-I remains the sole destructive engine;
- safe canonical `BackendProcessOwner` restart/result handoff;
- restart failure preserves C4-I truth and returns to maintenance exclusion;
- frontend remains unchanged.

Focused B2 tests and a B2 implementation lifecycle gate are included in this changeset. Their execution status is not claimed until exact-head commands actually run.

## Still blocked

```text
C4-II-B3 — not authorized
C4-II-C — not authorized
C4-III — not authorized
```

## Open product obligations

- exact-head verify B2 focused and regression suites;
- external isolated process smoke on the published B2 head;
- independent B2 `P0=0/P1=0/P2=0` audit;
- merge B2 only if all required evidence is green;
- lifecycle-close B2 before any B3 authorization;
- later B3 explicit destructive confirmation;
- later C4-II-C outcome/restart/support UX;
- C4-III end-to-end Restore closure;
- macOS packaging/update/install verification/full release-candidate smoke.
