# Deployment

MVP is local-first. User mode must not require Git, terminal, Python, Node.js or Docker.

## Current status

- launcher local runtime foundation exists;
- local FastAPI remains bound to `127.0.0.1`;
- user data remains outside repository/package;
- backup-before-migration remains part of startup;
- ordinary browser remains the product UI;
- final macOS `.app`/`.dmg` packaging is not implemented.

## Restore topology

```text
browser presentation
  ├── ordinary business API → FastAPI backend
  └── Restore control → launcher-owned 127.0.0.1:<ephemeral>
                         → A3 native macOS picker
                         → A1 non-destructive validation
```

## C4-II-A status

```text
PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

A3 uses exact `/usr/bin/osascript`, fixed Standard Additions `choose file`, no new dependency, launcher-private path and owned child quiescence.

A4 may now add only the browser bootstrap/session/presentation seam. The launcher may open the normal browser URL with control port + one-use bootstrap capability in the URL **fragment only**. The SPA must consume it once, remove it immediately and retain only run-scoped descriptors in `sessionStorage`.

No query-token transport, `localStorage` token, browser path/file fallback, FastAPI Restore mutation or destructive Restore authority is allowed.

C4-II-B remains separately not authorized.