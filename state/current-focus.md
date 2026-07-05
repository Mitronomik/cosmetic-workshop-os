# Current Focus

## Last completed

PR75 — Export API foundation — is implemented.

## Next allowed task

PR76 — Export UI.

Scope for PR76 should remain frontend-only unless the prompt explicitly says otherwise:

- consume existing `GET /api/exports/status`, `GET /api/exports`, and explicit-click `POST /api/exports`;
- show export status, local export directory, export history, and creation result in human-readable Russian UI;
- do not create exports on page load;
- do not add import, restore, CSV/XLSX/PDF export, download/delete endpoints, scheduled/cloud exports, migrations, arbitrary filesystem paths, or business-data mutations.
