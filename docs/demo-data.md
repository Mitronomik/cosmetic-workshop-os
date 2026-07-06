# Demo data mode

Demo data mode is a backend/API foundation for showing a non-technical user a safe example workspace for **Мастерская косметолога**.

## Safety contract

- Demo data is installed only by an explicit API request.
- Demo data is local-only and does not require internet access.
- PR84 installs demo data only into an empty business workspace.
- Demo data is never installed by migrations, startup initialization, onboarding, import, backup, or export.
- Demo install does not create backups or exports automatically.
- Demo install does not create production batches or write off production stock automatically.
- Demo install does not expand import apply targets.
- Demo records are visibly labeled with the stable prefix `Демо ·`.
- Demo-created records are tracked by table name and record id in `demo_data_records` under a `demo_data_sessions` session.
- Demo clear deletes only records tracked for the active demo session.
- Demo clear blocks if untracked working records reference tracked demo records, including direct references and generic references in alerts or purchase suggestions.
- Demo clear does not reset the database and does not delete real user data.

## Tracking tables

`demo_data_sessions` stores one install attempt/session with:

- `demo_version`;
- `status`: `active`, `cleared`, or `failed`;
- creation/clear timestamps;
- JSON summary.

`demo_data_records` stores every demo-created row by:

- `session_id`;
- `table_name`;
- `record_id`;
- human label.

Records are not tracked by name only. Names are user-visible labels; table/id tracking is the safety boundary.

## API

- `GET /api/demo-data/status` is read-only and reports whether demo data can be installed or cleared.
- `POST /api/demo-data/install` requires `confirm_install=true` and `understand_demo_data=true`.
- `POST /api/demo-data/clear` requires `confirm_clear=true`.

Conflict responses use Russian safety messages suitable for future UI.

## PR84 limitations

- No frontend UI is included.
- Demo data can be installed only when no non-demo business data exists.
- `GET /api/demo-data/status` returns `can_clear=false` when automatic clear is unsafe because working records still reference demo records.
- Before clearing, the user should manually resolve or delete working records that reference demo data.
- Alerts and purchase suggestions are not inserted directly by demo install; the dataset creates conditions that can be evaluated by existing explicit regeneration flows.
- Orders are not produced automatically. The user can manually run production readiness and confirmation later.
