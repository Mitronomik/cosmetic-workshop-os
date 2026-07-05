# Current Focus

PR76 — Export UI is complete in this branch.

Next recommended scoped PR: Import CSV/XLSX draft backend foundation.

Keep scope narrow:
- build import drafts through safe preview/confirmation architecture;
- do not implement restore from export;
- do not add export download/delete/CSV/XLSX/PDF/cloud/scheduled behavior unless explicitly requested;
- preserve local-first API-first boundaries and avoid direct frontend data-table inspection.
