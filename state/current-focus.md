# Current Focus

Current task: PR7 - Local runtime launcher MVP.

## Allowed scope
Minimal launcher/runtime foundation under `launcher/`, safe runtime configuration, explicit backend startup initialization in user mode, local backend process launch helper, optional browser opening, launcher tests, and related developer/user documentation.

## Do not touch
Final macOS `.app`/`.dmg`, installers, Electron, Docker, auto-update, cloud/mobile access, business UI, recipes, clients, orders, production, import/export features, new business tables, or migrations.

## Acceptance
Launcher MVP exists with localhost-only defaults, user data override works in tests, user-mode startup is explicit, backup-before-migration remains active through existing startup, no real user Documents directory is touched by tests, no new business tables are added, docs/state are updated, and checks/smoke are reported.
