# Handoff

Updated: `2026-08-07`

Current lifecycle authority: `docs/current-lifecycle.md`.
Current decision: `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md`.
Current ledger: `state/change-requests.md`.
Searchable history: `docs/history/README.md`.

## Current lifecycle

```text
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — AUTHORIZED — DECISION ONLY — NOT DECIDED
C4-II-A — PLANNED — BLOCKED BY CR-011 — NOT AUTHORIZED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Current action

PR #171 is the current task while it remains open:

```text
correct all audit findings
→ run documentation checks in a real checkout
→ repeat exact-head read-only audit
→ merge PR #171
```

Do not start CR-011 from the unmerged PR #171 branch.
Do not create a dependent CR-011 branch from the PR #171 head.
No runtime implementation belongs in PR #171.

## Authorized successor after PR #171 merges

After PR #171 merges, update `main` and create a fresh branch from merged `main`.
Only then begin the CR-011 decision-only task.

CR-011 must choose one concrete launcher Restore interaction architecture and
resolve screen ownership, picker ownership, command channel, exact-run security,
path privacy, backend lifecycle, dependencies, packaging consequences, cleanup,
and exact-head smoke. It does not authorize C4-II runtime implementation.

## Authority rule

ADR authority is resolved by scope and recency. ADR 0017 supersedes only dated
C4 implementation-status / authorization wording in ADR 0016. ADR 0016 remains
authoritative for the accepted launcher-assisted Restore product and safety
contract, including the twelve phases and recovery semantics.

## Future validation boundary

Future C4-II-A must use a launcher-owned, non-destructive boundary equivalent to
`prepare_restore_candidate(...)`. It must not execute Restore, create a durable
Restore operation, enter a Restore phase, create the pre-restore safety copy, or
mutate the working database. C4-II-B must later re-prove source or retained
candidate identity before destructive execution.

## Required PR #171 checks

Run in a real checkout:

```bash
git diff --check
python3 scripts/check_documentation_lifecycle.py
```

Also run the repository Markdown/link check if defined, then perform a fresh
independent exact-head read-only audit. PR #171 remains draft until that gate
passes.