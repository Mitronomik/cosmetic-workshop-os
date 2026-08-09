# Deployment

MVP is local-first. User mode must not require Git, terminal, Python, Node.js or Docker.

## Current status

- launcher local runtime foundation exists;
- local FastAPI remains bound to `127.0.0.1`;
- user data remains outside repository/package;
- backup-before-migration remains part of startup;
- ordinary browser remains the product UI;
- final macOS `.app`/`.dmg` packaging is not implemented.

## Restore lifecycle

```text
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B3 — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Implemented topology through B1

```text
launcher
→ ordinary backend
→ A2 exact-run 127.0.0.1:<ephemeral> control plane
→ A3 launcher-owned /usr/bin/osascript picker
→ A1 non-destructive validation + retained source proof
→ A4 fragment-only browser bootstrap + /backups/restore presentation
→ B1 same-HeldSource proof binding at C4-I intake
```

The browser remains presentation only. The bootstrap capability travels in the URL fragment only and is removed immediately. The run-scoped session token lives only in `sessionStorage`; same-tab replay metadata lives only in `history.state`.

## B2 deployment consequence

B2 adds no new service, port, daemon, helper executable or dependency. It extends the existing launcher-owned loopback control plane with one authenticated `/v1/restore/execute` command and adds launcher-runtime coordination inside the same process.

The same control plane must remain bound to the same ephemeral port while the ordinary backend is intentionally stopped by C4-I and while the launcher attempts the ordinary-backend restart handoff. No second control server/bootstrap is created for the destructive interval.

The destructive execution itself runs under the launcher main runtime owner path, not an HTTP worker. C4-I remains responsible for backend exclusion, safety copy, replacement, verification and rollback. The launcher runtime must track the current owned backend across the intentional stop/restart instead of treating the initial child process lifetime as the whole application lifetime.

B2 does not change frontend, packaging topology or the ordinary FastAPI business API. B3/C remain required before this becomes a complete user-visible Restore flow.
