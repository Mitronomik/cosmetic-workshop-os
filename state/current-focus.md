# Current focus

Slice A4 is DONE. Slice A5 is ACTIVE.

## Active task

**A5 — Human-readable local artifacts and data-location presentation**

Current focused implementation: present locally generated artifacts and the local data folder in user language on `/backups`, `/exports`, `/report-documents`, and the directly related local-data area of `/settings`.

Starting baseline is exact main `490b9506158c2a26d1fab9c85d0ba9f4c904cbae` (`Merge pull request #130 from Mitronomik/codex-ozds60`). The product owner supplied external GitHub verification that remote `main` still resolves to this SHA; the local working copy started from the same clean HEAD.

## A4 completion gate

Slice A4 responsive containment is complete. Final external exact-main cross-route smoke against `490b9506158c2a26d1fab9c85d0ba9f4c904cbae` returned `PASS — A4 CROSS-ROUTE EXACT-MAIN REGRESSION PASSED`. Verified routes included `/ingredient-lots`, `/orders`, `/clients`, `/inventory`, `/packaging-items`, passive `/ingredients`, passive `/recipes`, and passive `/client-recipes`. Evidence confirmed no document-level horizontal overflow, local table scrolling, first/final column reachability, action reachability, responsive create/edit/detail states, keyboard focus, no unexpected browser/request/page/HTTP failures, no SQLite mutations during passive verification, and exact-main postflight integrity.

## Scope

A5 changes only frontend presentation and project state for:

- `/backups`;
- `/exports`;
- `/report-documents`;
- the directly related local-data presentation on `/settings`.

The UI should emphasize filenames, artifact type, creation date, reason, size, `Сохранено локально`, and a human-readable application folder label. Full absolute paths remain available only as secondary technical support information.

## Non-goals

Do not implement restore, arbitrary file browsing, file move/rename/delete, backup scheduling, cloud upload/sync, new download behavior, backend storage changes, API schema changes, database schema changes, migrations, report calculation changes, PDF internals, import behavior, launcher behavior, or unrelated routes.

## Required verification

Run focused frontend presentation tests, existing relevant frontend tests, frontend build, focused backend tests for backups/exports/report documents/settings/profile, full backend exact-base and exact-head suites using local Git objects, repository hygiene checks, and browser smoke where the environment permits. Exact published-head smoke is required before marking the Draft PR ready; if the runner cannot publish or lacks a browser, report the limitation honestly.
