# launcher/AGENTS.md

Scope: everything under `launcher/`.

Local runtime rules:

- User mode must not require the end user to use terminal, Git, Python, Node.js or Docker.
- User data must stay outside the app, repository and package directory.
- The backend must listen on localhost only.
- The launcher must handle port conflicts with human-readable messages and recovery guidance.
- Migrations must be safe for existing local user data.
- In user mode, create a backup before schema migration.
- A package must not include a real user database, private backups, exports or logs.
- App restart must preserve user data in the configured user data directory.
- Startup and shutdown should be graceful and should not leave orphaned processes when avoidable.
