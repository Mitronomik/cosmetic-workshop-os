# Restore interaction and validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-09`

Normative sources: ADR 0016 for destructive Restore; ADR 0018 for launcher control/picker/exact-run browser session; current lifecycle plus the A/B slice plans for implementation status.

## Current lifecycle

```text
PR #180 — MERGED — C4-II-A4 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B2 — PLANNED — NOT AUTHORIZED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed A1→A4 architecture

```text
browser SPA /backups/restore
  ├── ordinary business API → FastAPI backend
  └── Restore control → launcher-owned 127.0.0.1:<ephemeral>
                         → A2 action/session coordinator
                           ├── A3 native picker
                           └── A1 validation worker
                         → C4-I intake/staging/validation
```

Browser owns presentation only. Launcher owns loopback control, picker, selected absolute path, candidate proof and all destructive authority.

A1 owns candidate preparation and retained proof. A2 owns exact Host/Origin, one-use bootstrap, session, 15s heartbeat / 60s expiry, strict replay/order and generation-gated worker publication. A3 owns exact `/usr/bin/osascript` `choose file`, typed cancel, absolute POSIX path and child quiescence. A4 owns fragment handoff, exact three-key `sessionStorage`, same-tab `history.state` replay metadata and the pathless `/backups/restore` UX.

A4 is now merged/exact-head verified. Its accepted screen remains non-destructive and exposes no final Restore action.

## Retained A1 proof

After successful A1 validation the launcher may retain, for the current active generation only:

```text
canonical absolute source path
SourceIdentity
full SHA-256
selection generation
compatibility
```

That proof is launcher-private. Filename, browser state, run/session token and `history.state` are not source proof and can never become destructive authority.

## Authorized B1 seam — proof binding at C4-I intake

C4-I already owns the complete destructive engine and already performs held-descriptor source intake, staging, validation, mandatory `before_restore` safety copy, durable phase transitions, replacement, verification and rollback.

B1 therefore adds **no second Restore pipeline**. It only adds an optional launcher-private expected-source gate at the existing C4-I intake boundary.

When an expected A1 proof is supplied, the comparison must happen against the same `HeldSource` descriptor returned by `open_selected_source(...)` and later used by C4-I staging:

```text
open_selected_source(...)
→ held.identity == expected SourceIdentity
→ held.revalidate()
→ held.assert_still_self_contained()
→ held.digest() == expected SHA-256 and exact expected byte count
→ held.revalidate()
→ held.assert_still_self_contained()
→ existing C4-I flow may continue
```

A path-only pre-check followed by a later re-open is forbidden because it leaves a substitution window between proof and destructive intake.

Any mismatch must fail closed before a durable `prepared` record exists. The ordinary result must use fixed nontechnical wording and expose no path, SQL, migration ID, stack trace or database contents.

Existing C4-I callers without an expectation retain current behavior. This is additive safety hardening for future C4-II-B, not a rewrite of C4-I.

## B1 non-goals

B1 does not authorize:

- browser destructive confirmation;
- a new A2/control HTTP command;
- backend shutdown wiring from browser/session;
- calling `execute_restore(...)` from a new user-facing coordinator;
- safety-copy creation merely to compare proof;
- a new staging or validation algorithm;
- durable phase/recovery changes;
- working-database replacement/migration changes;
- Restore AuditLog changes.

## Future B2/B3

B2 remains blocked until B1 is merged and closed. B2 must define the exact destructive launcher/session coordinator and command semantics, including one-shot replay behavior, current-generation ownership, backend stop/exclusion, session invalidation and result handoff while reusing existing C4-I `execute_restore(...)`.

B3 remains blocked until B2 is merged and closed. It will own the explicit destructive browser confirmation required by ADR 0016; browser state itself will still not be authority.
