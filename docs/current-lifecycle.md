# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-11`

ADR 0016 remains authoritative for destructive Restore. ADR 0018 remains authoritative for launcher control, picker and exact-run browser-session interaction.

## Current lifecycle

```text
PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED
PR #183 — MERGED — B2 AUTHORIZATION BASELINE
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
C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B3 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
installation verification — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

## Merged baseline and B2 closure

PR #182 reviewed B1 head `27726058af4f373ab65225ecf4d1a945f1c53067` merged as `5e13b50f1918dacbf8d54066c9156942a9adb895`.

PR #183 reviewed B2 authorization head `fa922f56c19a2dd33b6307ae0a197d476f91489b` merged as `4617b8c436eaa510fd545d863346595e2d808ea7`.

PR #184 reviewed B2 implementation head `1ae8bfcdf0f1f1798ce85eac0931925d029379c4` merged as `266c50a77e5f353fa77701cb854629a99460667f`.

## Accepted B2 evidence

- focused B2/runtime tests: **37 PASS** in the independent audit;
- launcher regression: **636 PASS**;
- backend regression: **1867 PASS**;
- full backend + launcher: **2503/2503 PASS**;
- frontend Restore regression: **16/16 PASS**;
- anti-hang owner-loop gate: **PASS**, autonomous, no manual `Ctrl+C`;
- corrected external exact-head isolated process smoke: **PASS**;
- external smoke proved production A4 handoff before bootstrap, authenticated `select → accepted → execute`, `restore_accepted / restoring`, same control-plane port through ordinary-backend stop and real C4-I verification lifetimes, durable phase `completed`, safe ordinary-backend restart, `restore_completed`, and isolated cleanup;
- independent audit: **P0=0 / P1=0 / P2=0 — AUDIT GATE PASS**;
- final no-change exact-head / clean-worktree gate: **PASS**.

The earlier eight-hour run that required repeated manual `Ctrl+C` is **INVALID / NOT A PASS**. The first external smoke runner is **INCONCLUSIVE RUNNER** because it consumed the one-use bootstrap before the production A4 handoff; it is neither product PASS nor product failure evidence.

## Closed B2 boundary

```text
browser/session
→ authenticated POST /v1/restore/execute(request_id, command_seq, generation)
→ exactly-next sequence consumed before business preconditions
→ current accepted control generation + current launcher-private retained A1 proof
→ one in-memory RestoreExecutionIntent
→ retained source authority invalidated immediately
→ pathless restoring
→ HTTP returns without C4-I
→ launcher main runtime consumes intent synchronously
→ ProofBoundRestoreRequest from launcher-private authority
→ existing C4-I execute_restore(..., LauncherLifecycleContext)
→ canonical ordinary-backend restart handoff when safe
→ pathless restore_completed / restore_failed / restore_blocked
```

The same `RestoreControlPlane` remains on the same ephemeral port while the ordinary backend is intentionally stopped. Session expiry cannot cancel accepted destructive work. Control generation and retained-proof generation remain separate domains. Browser `generation` is a stale-view guard only.

The accepted B2 production implementation is now a closed boundary and must remain byte-identical until a separately authorized lifecycle change says otherwise.

## Authorized successor — C4-II-B3

B3 is the only authorized next implementation slice.

B3 is **frontend-only** except focused frontend tests and lifecycle/checker/status documentation. It connects the accepted A4 browser session to the merged B2 `/v1/restore/execute` command through explicit human destructive confirmation.

B3 must:
- parse exactly the additional launcher states `restoring`, `restore_completed`, `restore_failed`, `restore_blocked`;
- add frontend action `execute` calling only `/v1/restore/execute`;
- require explicit confirmation for the current `accepted` candidate;
- send exact `request_id + command_seq + generation`;
- preserve the same generation on ambiguous execute replay;
- persist no source path/proof/digest/operation identity;
- keep filename display-only;
- provide no destructive cancellation once Restore is `restoring`;
- keep C4-II-C result/recovery semantics out of B3.

C4-II-C and C4-III remain **PLANNED — NOT AUTHORIZED**. Product Restore remains **NOT IMPLEMENTED**.
