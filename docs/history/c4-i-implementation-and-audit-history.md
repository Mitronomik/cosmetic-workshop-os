# C4-I implementation and audit history

Status: **HISTORICAL — NON-NORMATIVE**
Retained for traceability and repository search.
Current lifecycle authority lives in:

- `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md`;
- `docs/implementation-plan.md`;
- `state/current-focus.md`;
- `state/progress.md`;
- `state/handoff.md`.

This record must not override those current documents. It preserves the reasons
behind the final C4-I safety boundaries without restoring the multi-thousand-line
branch journals that previously lived in `state/`.

## Pull request and purpose

- Pull request: [#170 — C4-I — Implement launcher-owned Restore safety engine](https://github.com/Mitronomik/cosmetic-workshop-os/pull/170)
- Final independently reviewed and exact-head-tested implementation head:
  `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8`
- Merge commit on `main`:
  `e6997281d2e0268ce54184d988c114bac71c35e2`
- Merged: `2026-08-03T16:12:23Z`
- Additional file changes introduced by the merge commit: none

C4-I created internal launcher infrastructure for the accepted launcher-assisted
Restore contract. It implemented source intake and staging, candidate validation,
durable Restore operation state, the mandatory safety copy, database replacement,
verification, rollback, and startup recovery.

C4-I deliberately did **not** add a product file picker, Restore screen,
destructive confirmation, progress screen, completion screen, ordinary FastAPI
Restore endpoint, SPA Restore mutation, product CLI Restore workflow, or Restore
AuditLog event. User-facing Restore therefore remained `NOT IMPLEMENTED` after
PR #170 merged.

## Audit history

Six independent audit rounds found and closed twenty-four findings:

```text
5 + 5 + 7 + 3 + 2 + 2 = 24
```

Each round reviewed the correction published by the previous round. No round
required a new durable phase or a change to the accepted transition graph.

## Round 1 — five findings

### 1. Source WAL and journal safety

**Finding.** Sidecars were checked beside the already-staged candidate, where
source `-wal`, `-shm`, and `-journal` files could never be observed. A selected
source could therefore be staged without committed WAL contents.

**Correction.** Sidecars are checked beside the original selected source before
and after copying. The source is opened once with read-only and no-follow
semantics, copied through the held descriptor, and its identity and byte count
are re-proved.

### 2. Backend shutdown proof

**Finding.** A free port was not proof that the exact backend process had stopped.

**Correction.** The launcher owns the exact backend process handle and obtains a
typed stop proof only after the owned process has exited. No process-name search,
pattern kill, `pkill`, `pgrep`, `killall`, or port-based process termination is
used.

### 3. Canonical destructive paths

**Finding.** A self-comparison could authorize arbitrary caller-provided
replacement paths.

**Correction.** The caller supplies only the selected source. Every destructive
path is derived from launcher-owned runtime and workspace resolvers and is
re-derived and checked at destructive boundaries.

### 4. Rollback publication failure

**Finding.** Failure to publish `rollback_in_progress` could cause an unauthorized
transition attempt and obscure the actual durable phase.

**Correction.** The engine re-reads and reports the phase actually on disk,
preserves evidence, and blocks startup instead of inventing another transition.

### 5. Durable publication boundary

**Finding.** Parent-directory durability and ambiguous post-rename publication
outcomes were not handled strongly enough.

**Correction.** One publication primitive performs file flush, atomic replace,
target flush, and mandatory parent-directory flush. Failures are classified as
before, during, or after replacement; an ambiguous post-rename result is re-read
instead of assumed.

## Round 2 — five findings

### 6. Terminal `completed` publication

**Finding.** An ambiguous publication of `completed` could fall through to abort
logic and attempt the forbidden edge `completed → aborted`.

**Correction.** Terminal records are never transitioned again. A visible but not
fully confirmed terminal publication is handled without rollback or an illegal
edge.

### 7. Positive startup permission

**Finding.** Ordinary startup was permitted by a negative rule, which admitted
unresolved pre-replacement phases.

**Correction.** Startup uses one positive allow-list. Unknown or unresolved phases
never become safe merely because they are absent from an unsafe set.

### 8. Same-size source rewrite

**Finding.** A writer could modify the selected source in place while preserving
device, inode, size, and type.

**Correction.** Source identity includes high-resolution modification and change
timestamps, and staging performs two independent SHA-256 stability passes over
the same held descriptor.

### 9. Hard-crash backend orphan

**Finding.** A hard launcher crash destroyed the in-memory process handle, so a
still-running backend could appear absent to the next launcher.

**Correction.** The backend holds a canonical kernel-managed liveness lock for its
whole lifetime. A later launcher detects the live orphan through that lock.

### 10. Durability evidence

**Finding.** The documented full-flush fallback method was not actually retained
as evidence.

**Correction.** Safety-critical flushes record category, target kind, platform,
and method.

## Round 3 — seven findings

### 11. Retained backend exclusion and pre-import acquisition

**Finding.** The liveness lock was checked and released, reserving nothing during
safety-copy creation and replacement. A launcher-managed child also acquired the
lock only after application imports.

**Correction.** The launcher retains a maintenance lease through destructive and
verification work. Launcher-managed children use a pre-import entrypoint that
acquires the same canonical lock before importing the application and proves that
ownership through a bounded one-run pipe and token.

### 12. Typed blocked startup recovery

**Finding.** An orphaned backend could raise a launcher exception where startup
expected a typed recovery result, producing a traceback instead of a safe refusal.

**Correction.** Recovery returns a typed blocked result, starts no backend, opens
no browser, changes nothing on disk, and presents one fixed non-technical message.

### 13. Ambiguous operation identity

**Finding.** An ambiguous first `prepared` publication could read a previous
operation's terminal record and report it as the new attempt.

**Correction.** Operation identity is compared before any record is inherited.
A foreign record is not modified or reported as the current attempt.

### 14. `recovery_blocked` overwrite protection

**Finding.** A new attempt could replace a terminal `recovery_blocked` record,
losing the authoritative pointer to unresolved evidence.

**Correction.** Only `completed`, `aborted`, and `rolled_back` are replaceable
safe terminal states. Clearing `recovery_blocked` remains a separately authorized
support procedure.

### 15. Truthful unconfirmed-completion message

**Finding.** A durability-unconfirmed `completed` result used rollback wording,
claiming that previous data had been restored when no rollback occurred.

**Correction.** A fixed completion-durability category says only that the restored
data were verified but technical finalization could not be confirmed safely.

### 16. Pull-request evidence accuracy

**Finding.** The PR body described an earlier head and obsolete test counts.

**Correction.** Published evidence was updated to the exact correction head and
its actual results.

### 17. Test-node preservation

**Finding.** A pre-existing test node had been renamed instead of preserved.

**Correction.** The node ID was restored with corrected semantics, and later
evidence tracked baseline node preservation explicitly.

## Round 4 — three findings

### 18. Lease boundaries around verification

**Finding.** One broad release window covered migrations and two verification
backend cycles, leaving intervals where neither the launcher nor an exact child
held the canonical lock while database work could occur.

**Correction.** Startup and migrations run under the retained lease. Each
verification backend lifetime is a separate release, exact-child handshake,
check, stop, wait, and reacquire cycle. The lease is held between cycles and
before rollback can replace anything.

### 19. Recovery before ordinary port classification

**Finding.** A real orphan held both the canonical lock and configured port, but
the port check ran first and misreported it as an ordinary collision.

**Correction.** Launcher authority and Restore recovery ownership are resolved
before ordinary port classification. A same-port orphan receives the typed
Restore-blocked outcome rather than a generic port traceback.

### 20. Finding accounting

**Finding.** The PR body and supporting documents disagreed about finding totals.

**Correction.** The accounting was made explicit and consistent across the
published evidence.

## Round 5 — two findings

### 21. Retryable unrelated port collision

**Finding.** State-mutating recovery could run before discovering an unrelated
program on the configured port, turning a temporary environment problem into
terminal `recovery_blocked`.

**Correction.** Startup recovery is split into a non-mutating preflight and a
state-mutating half. The port is checked between them. A late collision is typed
as retryable, leaves the durable phase and evidence intact, publishes no
`recovery_blocked`, and can be retried after the port is freed.

### 22. Accurate handoff invariant

**Finding.** Documentation claimed continuous lock ownership even during the
bounded release-to-child scheduling interval.

**Correction.** The invariant is stated in terms of database access: no operation
that reads, migrates, verifies, or replaces the working database may run without
the launcher lease or the exact child's completed lock handshake. Nothing touches
the database during the bounded no-owner handoff interval.

## Round 6 — two findings

### 23. Real post-probe/pre-bind race

**Finding.** The parent probe released the port before the child performed the
real uvicorn bind. Another process could win that interval after the child had
already reported lock ownership, causing a false verification failure and
terminal `recovery_blocked`.

**Correction.** The exact child acquires the canonical liveness lock and binds the
actual configured listening socket before reporting readiness. Uvicorn serves the
same pre-bound socket through `Server.run(sockets=[...])`; there is no second bind.
Only `EADDRINUSE` produces the tokened `port-unavailable` result, before any
application import or database access.

### 24. Synthetic race evidence

**Finding.** The earlier test injected `BackendPortUnavailableError` directly and
proved routing, not reachability of the real socket race.

**Correction.** `test_restore_real_port_bind_race.py` uses the real parent, real
child entrypoint, real one-run handshake, real configured port, real competing
listener, and real bind refusal. Synthetic tests remain correctly labelled as
routing tests.

## Final load-bearing C4-I invariants

- Restore is launcher-assisted and destructive replacement is not an ordinary
  FastAPI or SPA mutation.
- The selected source is immutable, read-only input.
- Source staging uses one held descriptor, no-follow semantics, identity
  re-proof, sidecar checks, and two content-stability passes.
- The working database, backup directory, operation workspace, and locks are
  derived from launcher-owned canonical resolvers.
- The launcher retains backend exclusion whenever launcher code reads, migrates,
  verifies, or replaces the working database.
- An exact launcher-owned child proves both canonical lock ownership and actual
  listening-socket ownership before readiness is accepted.
- A verified `before_restore` safety copy is mandatory before replacement.
- Filesystem replacement and SQLite do not form one transaction.
- `replacement_intent` is recorded before the ambiguous replacement boundary and
  is treated conservatively after interruption.
- Publication uses atomic replacement plus file and parent-directory durability.
- Startup recovery runs before ordinary startup and follows one accepted recovery
  matrix.
- Retryable environment refusal is not persisted as a Restore phase or flag.
- `rolled_back` is failed Restore, never success.
- `recovery_blocked` never permits ordinary startup.
- The ordinary browser opens only after durable `completed`.
- No Restore AuditLog event is authorized.

## Accepted durable phases

The vocabulary remains exactly twelve values:

```text
prepared
source_staged
candidate_validated
safety_copy_verified
replacement_intent
replacement_committed
verification_in_progress
completed
aborted
rollback_in_progress
rolled_back
recovery_blocked
```

`phase` remains the sole authoritative lifecycle field. The transition graph,
terminal-state rules, and startup recovery matrix remain normative in
[`docs/decisions/0016-launcher-assisted-restore.md`](../decisions/0016-launcher-assisted-restore.md)
and [`docs/backup-and-restore.md`](../backup-and-restore.md).

## Final accepted evidence

Evidence accepted for the exact final implementation head
`ac95e2990efa979b3ded6cb48f91ddd0750aa7c8`:

| Check | Result |
|---|---|
| Full backend + launcher suite | `2398 passed` |
| Launcher suite | `531 passed` |
| Frontend `test:*` scripts | `21 / 21 passed` |
| Frontend production build | `PASS` |
| Ordinary launcher/product regression gate | `11 / 11 PASS` |
| PR-specific Restore smoke | `28 / 28 PASS` |
| Worktrees after exact-head smoke | clean |
| Owned runtime processes remaining | `0` |
| P0 findings at final merge gate | `0` |
| P1 findings at final merge gate | `0` |
| P2 findings at final merge gate | `0` |

These results belong to PR #170. They are not re-executed or relabelled by the
documentation-only PR #171.

## Full pre-compaction snapshots

The complete branch-era state journals remain available at the PR #170 merge
commit:

```bash
git show e6997281d2e0268ce54184d988c114bac71c35e2:state/current-focus.md
git show e6997281d2e0268ce54184d988c114bac71c35e2:state/progress.md
git show e6997281d2e0268ce54184d988c114bac71c35e2:state/handoff.md
```

They can be restored to a temporary worktree when deeper archaeology is required:

```bash
git restore \
  --source=e6997281d2e0268ce54184d988c114bac71c35e2 \
  -- state/current-focus.md state/progress.md state/handoff.md
```

Those snapshots contain obsolete active instructions from the period when PR
#170 was still open. They are evidence of that period, not current project
instructions.