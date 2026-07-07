# Handoff

## Last completed work

PR90 — Report document export UI + sidecar cleanup hardening.

## What changed

- Added `/report-documents` / «Документы отчетов» to the frontend navigation under «Данные и настройки».
- The new page calls only the implemented report document endpoints:
  - `GET /api/report-documents/status`
  - `GET /api/report-documents`
  - `POST /api/report-documents/reports/overview`
- Page load and refresh are read-only. Document creation is explicit and sends `format: "markdown"` plus an optional reason.
- The UI states clearly that Markdown is the only MVP format and PDF/DOCX are future work.
- The documents list shows metadata returned by the backend and does not preview raw file content or offer fake download/open actions.
- `/reports` now includes a contextual «Создать документ отчета» navigation action only; it does not create a document.
- `ReportDocumentService` cleanup now tracks current-operation document/metadata creation separately and only unlinks metadata when this operation actually created the sidecar.
- Added a regression test for metadata write failure before final sidecar creation; it verifies safe error, Markdown cleanup, no sidecar unlink attempt, and no business-table mutation.

## Manual smoke

Manual browser smoke was not run in this non-interactive environment. Recommended local smoke:
1. Start backend and frontend.
2. Open `/report-documents`.
3. Confirm status/list load and no document appears merely from page load.
4. Enter `еженедельная проверка` and click «Создать Markdown-документ».
5. Confirm the button disables while creating, success appears, and the new document appears in the list.
6. Refresh the list and confirm the document remains listed.
7. Open `/reports` and confirm «Создать документ отчета» only navigates to `/report-documents`.
8. Confirm exports/backups/imports/demo/help pages still load and no backup/export/import/demo action is triggered.

## Next recommended PR

Next implementation PR — Report PDF generation foundation, unless smoke finds UI issues. If smoke finds issues, fix the report document UI in the next implementation PR before adding PDF.
