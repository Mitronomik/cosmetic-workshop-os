# Handoff

PR93 implemented safe open/download workflow for generated report documents.

Changed behavior:
- `GET /api/report-documents/{document_id}/download` serves only known generated report documents from metadata.
- `disposition=attachment` downloads; `disposition=inline` opens PDFs inline. Markdown stays attachment.
- Unknown IDs, missing files, unsafe path metadata, filename/format mismatches, and unsupported dispositions return safe Russian errors.
- `/report-documents` lists generated documents with `Открыть PDF`, `Скачать PDF`, or `Скачать Markdown` actions.
- `/reports` still only navigates to `/report-documents` and does not create files.

Manual smoke was not run because this non-interactive session has no browser download/viewer confirmation path. Recommended manual smoke:
1. Start backend and frontend.
2. Open `/report-documents` and confirm status/list load.
3. Create Markdown and click `Скачать Markdown`.
4. Create PDF when available and click `Открыть PDF`, then `Скачать PDF`.
5. Open `/reports` and confirm `Открыть документы отчетов` only navigates.
6. Reload `/report-documents` and confirm no new files are created.
7. Call unknown/path-traversal download URLs and confirm safe 404/422 responses.

Next recommended task: PR94 — Settings UI foundation, unless smoke finds document workflow follow-up fixes.
