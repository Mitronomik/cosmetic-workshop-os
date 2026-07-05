# Current focus

PR74 — Backup UI is implemented.

## Completed in PR74
- Added frontend `/backups` workspace and navigation item «Резервные копии».
- Consumes only PR73 backup API endpoints: `GET /api/backups/status`, `GET /api/backups`, and explicit-click `POST /api/backups`.
- Shows database location/existence/size, backup folder location/existence, backup count, latest backup, and backup history.
- Supports manual backup creation with reason presets and a max-80-character custom reason.
- Updated dashboard backup reminder so it navigates to the backup workspace instead of promising a future backup/export screen.

## Out of scope / not added
- No restore, download, delete, scheduled backups, cloud backup, export, import, arbitrary path input, polling, notifications, automatic backups, backend endpoints, migrations, or business mutations were added.

## Next recommended PR
- Export foundation or Import/Export preparation, depending on the next roadmap slice.
