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
PR #180 — MERGED — C4-II-A4 EXACT-HEAD VERIFIED
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B2 — PLANNED — NOT AUTHORIZED
C4-II-B3 — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Implemented topology through A4

```text
launcher
→ ordinary backend
→ A2 exact-run 127.0.0.1:<ephemeral> control plane
→ A3 launcher-owned /usr/bin/osascript picker
→ A1/C4-I non-destructive validation
→ A4 fragment-only browser bootstrap + /backups/restore presentation
```

The browser remains presentation only. The bootstrap capability travels in the URL fragment only and is removed immediately. The run-scoped session token lives only in `sessionStorage`; same-tab replay metadata lives only in `history.state`.

## B1 deployment consequence

B1 is internal launcher/C4-I safety hardening only. It adds no service, port, process, browser transport, dependency or packaging requirement. It must not broaden the A2 HTTP vocabulary or change ordinary backend startup.

B1 binds an optional A1 expected source proof to the exact held descriptor already opened by C4-I. B2/B3 destructive runtime wiring remains not authorized.
