# ADR - SQLite backup consistency and manual-backup AuditLog coverage

## Status

`ACCEPTED` — 2026-08-02. Resolves `CR-004`, which was `needs evidence` since
2026-07-26, and unblocks `C3-II-B3 — Manual backup AuditLog coverage`.

| Item | Status |
|---|---|
| `CR-004` — SQLite backup transaction consistency | `ACCEPTED — PRODUCT DEFECT — BACKUP CONSISTENCY (HIGH)` |
| `C3-II-B3` — manual backup AuditLog coverage | `IMPLEMENTED ON PR BRANCH — NOT MERGED` |
| Restore | not implemented, not authorized |
| C4 | inactive |
| Product release readiness | not claimed |

This ADR does not reopen `CR-005`, `CR-006`, `CR-009`, ADR 0013 or ADR 0014.

## Context

`POST /api/backups` and the automatic `before_migration` startup backup both
used one low-level service, and that service copied the live SQLite main
database file with `shutil.copy2`:

```text
normalize human reason
→ backup_sqlite_database(...)
→ shutil.copy2(source_database, final_backup_path)
→ stat the final backup
→ re-scan the backup directory
→ build the create response from the listing metadata
```

The application does not pause writers during a backup, ordinary repositories
open their own SQLite connections, and no journal mode is forced anywhere in the
codebase. `CR-004` asked whether that copy can be trusted.

## Evidence

### Provenance

| Item | Value |
|---|---|
| Repository SHA under test | `844526ae4057a454312f790abcaf21be518cdbd9` (merged `main`, PR #166 merge commit) |
| Python | `3.12.10` |
| `sqlite3.sqlite_version` | `3.49.1` |
| Default journal mode | `delete` — the application forces no mode |
| Default `busy_timeout` | `5000` ms, from `sqlite3.connect(timeout=5.0)` |

The harness ran outside the repository against the exact checked-out production
service, on isolated user-data directories with no real user data, using real
SQLite connections and controlled writer threads. Faults were injected only at
named boundaries. The harness is not committed; its findings are pinned by
`backend/app/tests/test_backup_consistency.py`, which exercises the shipped
engine directly.

### Quiescent raw copy — the control

25 committed rows, all writers closed. The copy opened independently, returned
`quick_check = ok` and `integrity_check = ok`, contained all 25 rows, and left
the source byte-identical. **The raw copy is correct when nothing is writing.**
That is the entire extent of its correctness.

### WAL, committed but uncheckpointed

`journal_mode = WAL`, `wal_autocheckpoint = 0`, 200 rows committed and visible
through an ordinary connection to the source, a 45 352-byte `-wal` present.

| Observation | Value |
|---|---|
| Committed rows in source | 200 |
| Committed rows in the copy, read in isolation | **0** |
| `quick_check` / `integrity_check` on the copy | `ok` / `ok` |
| Migrations present in the copy | all 20 |
| Source business data changed | no |

The concurrent-writer run reproduced the same result at scale: 954 committed
transactions, and every one of 10 successive raw snapshots contained **zero**
rows.

This is **omission of committed data**, not corruption. The file is structurally
perfect and transactionally stale. It is also not independent: the copy inherits
the WAL-mode header, so reading it recreates `-wal`/`-shm` sidecars, and what it
reports is the last checkpointed state rather than the committed state.

### Rollback journal, transaction in flight

12 rounds, a large transaction spilling pages into the main file while the raw
copy ran. **12 of 12** copies contained **two different transaction states at
once**, with `quick_check = ok` and the row count intact. On the rounds where the
writer subsequently **rolled back**, the copy contained rows from a transaction
that never existed in the source.

Reachability was then checked with the **stock page cache** (`cache_size =
-2000`) and no PRAGMA tuning at all, on a 42 MB database with a 40 000-row
transaction — the size an import apply or bulk edit reaches. Same result: mixed
state, never-committed rows present, `quick_check = ok`.

This is **inclusion of uncommitted and mixed transaction data**, not corruption.

### Corruption — one reproduced scenario

Raw copy taken while an open transaction had spilled 4 000 uncommitted rows:

| Observation | Value |
|---|---|
| `quick_check` | `wrong # of entries in index idx_ingredients_category` |
| Committed rows present | 3 494 of 4 000 — **506 missing** |
| Never-committed rows exposed | 465 |

**Corruption is claimed only for this scenario**, and only because a structural
check actually failed. The WAL and rollback-journal findings above are omission
and mixed state respectively, and are deliberately not described as corruption.

### Concurrent committed writers

Each writer transaction inserted a matched pair into two tables; a snapshot
holding one half without the other has captured part of one transaction.

| Engine | Journal mode | Committed | Torn pairs | Snapshot rows, first → last |
|---|---|---|---|---|
| raw copy | `delete` | 783 | 0 | 211 → 729 |
| raw copy | `WAL` | 954 | 0 | **0 → 0** |
| online backup | `delete` | 735 | 0 | 190 → 677 |
| online backup | `WAL` | 961 | 0 | 246 → 885 |

Small paired transactions do not tear under either engine. The raw WAL row is the
finding: nothing torn because nothing at all was captured.

### Uncommitted data exclusion

| Engine | Open transaction | Committed present | Uncommitted exposed | `quick_check` |
|---|---|---|---|---|
| raw copy | spilled | 3 494 / 4 000 | 465 | **failed** |
| raw copy | cached only | 4 000 / 4 000 | 0 | `ok` |
| online backup | cached only | 4 000 / 4 000 | 0 | `ok` |
| online backup | spilled (source locked) | — | — | **refused, no file produced** |

The bounded online backup refuses rather than producing a wrong snapshot.

### Online Backup API

`sqlite3.Connection.backup` includes committed WAL state, excludes uncommitted
state, keeps transactions atomic, produces a destination with **no** `-wal`,
`-shm` or `-journal` sidecar that opens independently with `quick_check = ok`,
and leaves the source **byte-identical** (SHA-256 unchanged) with its business
rows unchanged.

**No source mutation was observed for either engine, in any scenario.**

### Busy and lock behaviour — the one hazard in the replacement

| Case | Implementation | Lock held | Outcome | Elapsed |
|---|---|---|---|---|
| short lock | plain `backup()` | 1 s | completed | 1.00 s |
| long lock | plain `backup()`, `timeout=2.0` | 25 s | **never returned** | killed at 12 s |
| long lock, no retry sleep | plain `backup()`, `timeout=2.0` | 25 s | **never returned** | killed at 12 s |
| long lock | bounded candidate | 25 s | `database is locked` | 2.08 s |
| long lock, WAL source | plain `backup()` | 8 s | completed | 0.006 s |

CPython retries `sqlite3_backup_step` for as long as it reports `SQLITE_BUSY` or
`SQLITE_LOCKED`. The source connection's own busy timeout bounds each *step* but
not the *loop*, and disabling the retry sleep does not help. A callback probe
confirmed the mechanism precisely: the first step blocked for 5.18 s (the source
busy timeout), returned `SQLITE_BUSY`, and CPython went round again.

**The plain call is unbounded and must not be used as-is.**

### Destination failures

Injected at named boundaries, against the candidate engine:

| Failure point | File remains | Size | Valid application DB | Listed |
|---|---|---|---|---|
| destination connect | no | — | — | no |
| backup step (aborted mid-copy) | **yes** | **0** | no | **yes** |
| destination close | yes | full | yes | yes |
| final size read | yes | full | yes | yes |

The aborted case is the important one: **a zero-byte file is a valid empty SQLite
database and returns `quick_check = ok`**, while being listed as a backup. Size,
schema and embedded-identity checks are therefore load-bearing, and the engine
must remove its own partial destination.

### The current create-response directory re-list

Driven through the real FastAPI route, with faults at `pathlib.Path.stat`,
`pathlib.Path.iterdir` and the named `list_backup_files` seam:

| Injected fault | Result |
|---|---|
| listing omits everything | `IndexError` escapes the route |
| listing returns only a foreign file | `RuntimeError: coroutine raised StopIteration` |
| `stat` fails on the exact created file | `OSError` escapes the route |
| directory iteration fails | `OSError` escapes the route |

Four complete backups were on disk at the end. Re-armed so the fault fires
**only after** `backup_sqlite_database` returns successfully, the route still
raised while a complete 417 792-byte `quick_check = ok` backup existed.

**False total failure after a verified backup is reachable**, and this is the
same class of defect ADR 0014 corrected for JSON exports.

### Automatic pre-migration backup

Startup on a database frozen at `0019`:

| Observation | Value |
|---|---|
| Ledger table before startup | absent |
| Automatic backup created | yes, `before_migration` |
| Snapshot migration head | `0019_...` — **no ledger table inside** |
| Live migration head after startup | `0020_artifact_audit_operations` |
| Ledger rows created | 0 |
| `backup.created` events | 0 |

It runs before migrations, cannot depend on `0020`, and is not audited.

## The CR-004 question, answered

> Can `shutil.copy2` of the active SQLite main file guarantee a complete,
> transactionally consistent, independently restorable snapshot of committed
> application state under all supported local runtime conditions?

**No.**

| Impact category | Verdict |
|---|---|
| Silent omission of committed data | **confirmed** — WAL, total omission, `quick_check = ok` |
| Mixed transaction state | **confirmed** — 12/12, stock page cache |
| Inclusion of never-committed data | **confirmed** |
| Corrupt backup | **confirmed in one scenario** (spilled uncommitted transaction) |
| Dependence on missing WAL/journal | **confirmed** |
| False success / false total failure | **confirmed** (create-response re-list) |
| Source mutation | **not observed** in any scenario |
| Writer blocking | **not observed** for the raw copy |

Classification: **`PRODUCT DEFECT — BACKUP CONSISTENCY`**, severity **`HIGH`**.

High because the affected artifact is the user's only recovery path, the failure
is silent, and it is reachable with default settings. It is **not** live-data
loss: the source database is never modified, and no workshop record is harmed by
taking a backup. The damage is discovered only when the backup is needed.

## Decision

### Snapshot semantics

A successful SQLite backup is:

```text
one transactionally consistent snapshot of committed source-database state
at one instant during the backup operation
```

It includes only committed data; never part of one SQLite transaction; does not
promise the exact instant the user clicked; may reflect commits completed before
its snapshot point and exclude commits completed after it; is independently
openable without the source WAL or rollback journal; is **not** required to be
byte-identical to the source; and never mutates the source's business data.

### Mechanism

`sqlite3.Connection.backup` through the SQLite Online Backup API, with
`pages=-1` so the whole database is copied in a **single** backup step under one
read lock — the destination can then only ever be one committed point.

`shutil.copy2` is not used for SQLite contents. `-wal`, `-shm` and `-journal`
files are never copied or guessed at. There is no application-global write
freeze, no background worker, no scheduled or cloud backup, and no Restore.

### Bounded busy behaviour

The source connection uses `timeout=5.0` — the repository's existing implicit
convention, since `sqlite3.connect` already defaults to it everywhere else — and
a progress callback refuses `SQLITE_BUSY` and `SQLITE_LOCKED` instead of
retrying. One busy wait, then a truthful `BackupBusyError`.

**Only those two statuses.** Every other unsuccessful result — `SQLITE_NOTADB`,
an I/O error, a full disk — is a real fault that CPython already raises as
itself. Relabelling those as "the database was busy" would be untrue and would
hide the harder problem.

### Manual versus automatic backup

Both use the same engine. Manual backup is user-initiated, uses the CR-009
ledger and AuditLog, and carries `audit_status` / `audit_message`. The automatic
`before_migration` backup stays before migrations, creates no ledger row, is
never audited, and cannot depend on `artifact_audit_operations` existing.

### Snapshot position relative to the ledger

```text
reserve the exact final backup filename
→ commit the prepared manual_backup ledger row
→ create the SQLite snapshot
→ verify the exact backup
→ finalize AuditLog and live ledger state atomically
```

The snapshot therefore **contains its own matching ledger row** in
`status = prepared` with `audit_log_id IS NULL`, and no `backup.created` event
for itself.

This is intentional and is the load-bearing property of the whole slice. A
backup is a SQLite database, so unlike a Markdown document or a JSON export it
can carry proof of which operation produced it. An unrelated but perfectly
healthy database sitting at the reserved path passes every structural check
there is; only the embedded row distinguishes them.

The completed backup is **never** rewritten afterwards to promote that row to
`audited`. Doing so would mutate a verified artifact after the fact and destroy
the durable pre-artifact preparation guarantee. A restored database therefore
contains one unresolved `prepared` operation, which normal post-migration
startup reconciliation handles as it handles any other. Restore is out of scope.

### Exact verification

`quick_check = ok` alone never authorizes an audit event. A valid manual backup
must additionally: pass shared safe-name validation and the strict generated
filename grammar; resolve inside the configured backup directory and not through
an escaping symlink; exist as a regular, non-empty file; open read-only; contain
`schema_migrations`, `artifact_audit_operations` and migration `0020`; and
contain exactly the matching embedded operation row — same `operation_id`,
`artifact_kind = manual_backup`, `audit_action = backup.created`, exact
`primary_filename`, `companion_filename IS NULL`, `status = prepared`,
`audit_log_id IS NULL`.

Verification never writes to, migrates or modifies the backup, never compares its
historical business rows with the live database, and never exposes its contents
through AuditLog.

### Partial success, and what is *not* partial success

Verification and AuditLog persistence are separate results and are never
collapsed. Finalization therefore reports three distinct outcomes — `recorded`,
`audit_pending` and `artifact_invalid` — rather than an ID-or-nothing.

A **verified** backup plus a failed AuditLog finalization returns HTTP `201`
with `audit_status: pending`, keeps and lists the backup, leaves the operation
unresolved and counted, and never deletes the backup, re-POSTs or reports total
failure.

An artifact that did **not** pass verification is not a created backup at all.
It must never return `201`, never say `Резервная копия создана.`, never write a
`backup.created` event, and never be described as merely awaiting a Journal
entry — telling a user their data is safely copied when nothing proved that is
the worst outcome available here. It returns one fixed safe Russian error
carrying no filename, path, operation ID, SQLite message, verifier-internal
reason or stack trace.

The artifact is left on disk untouched. This operation cannot prove it owns what
is at that path — establishing exactly that is what verification failed to do —
so deleting it could destroy a file belonging to something else. The ledger row
is left unresolved and counted: neither audited nor abandoned, so the operation
stays diagnosable and eligible for bounded reconciliation.

A ledger-preparation failure before the snapshot returns the accepted structured
HTTP `500` with no backup, no event and no committed operation.

The five create failure modes stay distinct in the API, and a test pins that:

| Condition | Result |
|---|---|
| source missing | `404`, fixed Russian text |
| tracking could not be prepared | `500` `artifact_audit_tracking_unavailable` |
| snapshot could not be produced | `409` `backup_source_busy` / `backup_failed` |
| artifact did not verify | `500` `backup_verification_failed` |
| verified, AuditLog failed | `201` `audit_status: pending` |
| verified and audited | `201` `audit_status: recorded` |

`BackupError` may embed an absolute database path and a SQLite message, so its
text is never propagated to a response; it stays available through exception
chaining, logs and tests.

### Destination ownership

The engine writes into a file it creates exclusively (`O_CREAT | O_EXCL`) in the
destination directory, then publishes it onto the reserved name with `os.link`,
which is atomic and **refuses** when the target exists.

`exists()` followed by an open is not an ownership guarantee: another process can
create the destination in between, and the Online Backup API would then overwrite
a foreign file while failure cleanup unlinked one this operation never created.
The no-replace decision therefore belongs to the same syscall that publishes. A
plain rename is rejected for the same reason — it silently replaces.

Consequences: no foreign file is ever overwritten or unlinked; the published path
is exactly the filename committed to the ledger; the scratch file carries a
suffix the listing ignores, so an interrupted operation cannot leave a misleading
successful-looking backup; and cleanup only ever removes the engine's own scratch
file.

## Rejected alternatives

1. **Continue using `shutil.copy2`.** Reproducibly omits all committed WAL data
   and produces mixed transaction state with a green `quick_check`.
2. **Copy the main database plus guessed journal files.** No atomic multi-file
   read exists; the set is racy and version-dependent, and a mismatched pair is
   worse than either file alone.
3. **Globally stop all application writes.** A user-visible freeze in a
   local-first desktop app, to fix something SQLite already solves correctly.
4. **Use frontend coordination as a database lock.** The frontend is not the only
   writer and cannot see SQLite's locks.
5. **Treat `quick_check = ok` as proof of completeness.** Directly disproven: an
   empty file and a totally stale WAL copy both return `ok`.
6. **Require byte-identical source and backup.** The Online Backup API
   legitimately rebuilds page layout; demanding equality would reject correct
   snapshots and re-introduce the raw copy.
7. **Add a generic background backup service.** Out of scope, unbounded, and not
   needed for a bounded two-moment retry.
8. **Add another ledger.** CR-009's ledger already reserves `manual_backup`.
9. **Add a sidecar for AuditLog identity.** The snapshot already carries its own
   identity; a sidecar adds a second file that can be lost independently.
10. **Implement Restore.** Separate, unauthorized, and not required to make
    backups correct.

## Consequences

- Backups are now transactionally consistent and independently openable; a
  backup is no longer a byte-level clone, and nothing may assert that it is.
- A backup source must be a real SQLite database. Tests that used literal bytes
  as a stand-in were updated to real migrated databases; that stand-in was only
  ever valid because the old code copied bytes it did not understand.
- A locked source now fails a manual backup in bounded time with a safe message,
  where it previously produced a wrong file.
- `POST /api/backups` no longer re-lists the backup directory, removing the
  reachable false-total-failure path.
- The `/backups` screen gains a separate Journal-pending warning region.
- Manual backups appear in the Journal as `Резервная копия создана`, with no
  filename, path, reason, size or migration information.

## Non-goals

Restore; scheduled backup; cloud backup; retention or cleanup policy; auditing
automatic `before_migration` backups; auditing or backfilling historical backup
files; renaming or rewriting legacy backups; changing CR-005 or the backup reason
labels; backup download or delete; migration `0021`; any change to migration
`0020`; C4 activation; any claim of product release readiness.
