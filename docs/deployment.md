# Deployment

MVP is local-first. User mode must not require Git, terminal, Python, Node.js or Docker.

## Current status

- launcher local runtime foundation exists;
- local FastAPI remains bound to `127.0.0.1`;
- user data remains outside repository/package;
- backup-before-migration remains part of startup;
- ordinary browser remains the product UI;
- final macOS `.app`/`.dmg` packaging is not implemented.

## C4-II-A status

```text
PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED
PR #179 — MERGED — A3 CLOSED / A4 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Restore topology now implemented through A4

```text
launcher
→ ordinary backend
→ A2 exact-run 127.0.0.1:<ephemeral> control plane
→ A3 launcher-owned /usr/bin/osascript picker
→ A1/C4-I non-destructive validation
→ A4 fragment-only browser bootstrap + /backups/restore presentation
```

A4 launcher handoff transports the ephemeral control port and one-use bootstrap capability in the URL **fragment only**, never the query. The bootstrap transport is fragment only and never a query parameter. If the handoff cannot be built safely, the launcher closes Restore control authority and opens the ordinary product URL.

The SPA removes the fragment immediately, exchanges it once, and retains only `control_origin`, `run_id` and the session token in `sessionStorage`. Non-secret strict-command replay metadata lives only in same-tab `history.state`. No token is written to `localStorage` or the ordinary backend API.

Production browser Restore remains presentation only. The browser never owns a local file path and never falls back to upload/file-input authority.

C4-II-B destructive Restore remains separately not authorized.
