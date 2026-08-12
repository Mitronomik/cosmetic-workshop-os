# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The user product must run without requiring GitHub, Git, Python, Node.js, Docker or a terminal.

## Current product status

```text
PR #188 — MERGED — C4-II-C EXACT-HEAD VERIFIED
PR #187 — MERGED — C4-II-C AUTHORIZATION BASELINE
PR #186 — MERGED — C4-II-B3 EXACT-HEAD VERIFIED
PR #185 — MERGED — B3 AUTHORIZATION BASELINE
PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED
PR #183 — MERGED — B2 AUTHORIZATION BASELINE
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-C — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-III — AUTHORIZED NEXT — NOT IMPLEMENTED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

PR #188 reviewed exact C4-II-C head `1df21915fdcf4a708dc778a0e762d64830b5b880` and merged as `6294f0044c792ced3ac56d213ea5333e33062f12` at `2026-08-11T17:25:11Z`.

## Closed Restore implementation chain through C4-II-C

C4-I remains the only destructive Restore engine. B1 binds launcher-private retained source proof to C4-I intake. B2 owns authenticated one-shot `/v1/restore/execute` authority transfer and ordinary-backend restart handoff. B3 owns explicit browser confirmation and exact destructive replay. C4-II-C owns truthful final/recovery presentation without changing Restore authority.

Accepted C4-II-C evidence on the reviewed head:

- `git diff --check` PASS;
- lifecycle checker PASS;
- frontend install/build PASS with 0 vulnerabilities;
- focused Restore control suite **34/34 PASS**;
- browser smoke v5.4 PASS, including real resume-without-replay final-state precedence, true 401/409 invalidation, ambiguous execute and narrow layout;
- fresh independent audit **P0=0 / P1=0 / P2=0 — PASS**;
- final no-change exact-head gate PASS;
- final local and remote head unchanged.

The browser still has no filesystem/source authority. No source path, proof, digest, operation ID, database path, backup path or lock path crosses the browser boundary. No `/v1/restore/confirm` endpoint exists.

## Authorized next work

**C4-III — Restore end-to-end verification and lifecycle closure** is the only authorized next Restore slice.

Its purpose is verification and closure of the already-merged Restore chain: current-schema and supported older-schema Restore, rejection paths, interruption, rollback, repeated launch, source immutability, safety-copy retention and lifecycle closure.

C4-III does **not** authorize a new Restore engine, endpoint, browser filesystem authority, destructive command, packaging/update redesign or hidden product-behavior change. If verification finds a product defect, fix it in a separate bounded defect PR and rerun the affected exact-head verification before C4-III can close.

Restore remains **NOT IMPLEMENTED** until C4-III itself completes and lifecycle closure is accepted. Product release readiness remains **NOT CLAIMED**.

## Restore authority

- ADR 0016 — destructive Restore safety/state machine;
- ADR 0018 — launcher control/picker/exact-run browser-session architecture;
- ADR 0017 — C4 split and C4-III verification/lifecycle-closure purpose;
- `docs/current-lifecycle.md` — current lifecycle authority;
- `docs/c4-ii-b-implementation-slices.md` — closed B1→B3 contract;
- `docs/restore-interaction-and-validation-session.md` — active browser/control interaction profile.
