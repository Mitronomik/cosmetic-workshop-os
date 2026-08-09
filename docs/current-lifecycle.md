# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-09`

ADR 0016 remains authoritative for destructive Restore. ADR 0018 remains authoritative for launcher control, picker and exact-run browser-session interaction.

## Current lifecycle

```text
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B3 — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
installation verification — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

## B1 closure evidence

PR #182 reviewed head `27726058af4f373ab65225ecf4d1a945f1c53067` merged as `5e13b50f1918dacbf8d54066c9156942a9adb895`.

Accepted evidence:

- documentation lifecycle PASS;
- base `RestoreRequest` selected-source-only contract PASS;
- focused B1 10/10;
- Restore privacy 10/10;
- full backend + launcher 2480/2480;
- external exact-head A1-source-substitution smoke PASS;
- exact worktree/head remained clean;
- independent audit `P0=0 / P1=0 / P2=0`.

B1 is now closed. `launcher/restore/contracts.py`, `engine.py`, `source_proof.py`, `staging.py` and A1 form the merged source-proof boundary. C4-I remains the only destructive engine.

## Closed A1→B1 boundary

```text
A1 validates and retains launcher-private source path + SourceIdentity + SHA-256
→ B1 ProofBoundRestoreRequest carries non-path ExpectedSourceProof
→ C4-I opens source once
→ B1 re-proves same HeldSource identity/self-containment/full digest
→ same HeldSource enters unchanged C4-I staging
```

Browser filename/session/generation are never source proof. Base `RestoreRequest` remains selected-source-only. The proof subtype contains no target path.

## Authorized B2 boundary

Only **C4-II-B2 — launcher destructive coordinator/control command** is authorized next.

B2 must add a single authenticated `/v1/restore/execute` command with exact body `request_id`, `command_seq`, `generation`. The command may transfer only current launcher-private A1 authority into one in-memory execution intent. It may not accept a path/proof/digest from browser.

The HTTP/session layer must not call C4-I. The main launcher runtime loop owns the execution intent and invokes existing `execute_restore(ProofBoundRestoreRequest(...), context)` exactly once.

The same loopback control plane remains alive on the same ephemeral port while C4-I intentionally stops the ordinary backend. Heartbeat/state remain serviceable. Browser/session cancellation or expiry after accepted execution cannot cancel destructive Restore.

After C4-I returns, the main launcher runtime owns ordinary-backend restart handoff. A safe C4-I result is not reinterpreted or rolled back merely because ordinary backend restart fails. B2 publishes only fixed pathless control state and leaves full outcome UX to later C4-II-C.

Exact B2 semantics, allowed paths, tests and prohibitions are normative in `docs/c4-ii-b-implementation-slices.md`.

## Successor gate

B3 remains **PLANNED — NOT AUTHORIZED**. B2 must be implemented in one bounded PR, exact-head tested, externally smoked, independently audited, merged and lifecycle-closed before B3 may be authorized.

C4-II-C and C4-III remain blocked. Product Restore is still **NOT IMPLEMENTED**.
