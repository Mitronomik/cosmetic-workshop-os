# Handoff

PR93 docs follow-up updated `docs/frontend-concept.md` so the frontend concept no longer describes report documents as Markdown-only or PDF future-only.

Current documented behavior:
- `/report-documents` is the user-facing route for generated report documents.
- Markdown generation is always available.
- PDF generation is shown only when backend status advertises local PDF support.
- DOCX remains unsupported.
- Generated files are opened/downloaded only through `GET /api/report-documents/{document_id}/download`.
- The frontend does not construct absolute local paths, create object URLs, or browse arbitrary files.
- `/reports` only navigates to `/report-documents` and does not create files.

No backend or frontend code was changed in this follow-up.

Next recommended task: PR94 — Settings UI foundation, unless smoke finds document workflow follow-up fixes.
