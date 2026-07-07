# Current focus

PR92 follow-up is implemented: PDF availability is deterministic, tests do not depend on host system fonts, and report-document docs have been corrected.

The next implementation PR should be **PR93 — Report PDF UI polish / download-open workflow**, unless PR92 smoke finds PDF generation or report document UI issues. If smoke finds issues, the next PR should be **PR93 — Report PDF generation follow-up fixes**.

Scope guard for the next session:
- Do not add DOCX, invoices, acts, labels, certificates, recipe technical cards, accounting/tax reports, charts, scheduled jobs, cloud sync, AI/RAG, or template editing.
- Do not create PDFs automatically from page load or from `/reports`.
- Keep PDF support TTF-only unless a future task explicitly adds and tests TTC parsing.
- Keep report values backend-owned; frontend should only display backend responses.
