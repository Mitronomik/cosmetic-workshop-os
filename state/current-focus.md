# Current Focus

PR78 — Import draft UI / preview UI is implemented in this branch.

Scope now remains limited to validating and reviewing the frontend Import workspace at `/imports`:

- consumes PR77 draft-only import API;
- supports target listing, explicit CSV/XLSX draft upload, draft listing, draft detail, preview rows, validation issues, and cancellation;
- does not implement import apply/confirmation, mapping editor, OCR, PDF/image import, automatic backup/export, or writes to real business tables.

Next recommended PR after smoke feedback: Import validation refinement or Import apply design/backend.
