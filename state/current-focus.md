# Current focus

PR92 is implemented: Report PDF generation foundation plus the `/reports` navigation copy fix.

The next implementation PR should be **PR93 — Report PDF UI polish / download-open workflow**, unless PR92 smoke finds PDF generation or report document UI issues. If smoke finds issues, the next PR should be **PR93 — Report PDF generation follow-up fixes**.

Scope guard for the next session:
- Do not add DOCX, invoices, acts, labels, certificates, recipe technical cards, accounting/tax reports, charts, scheduled jobs, cloud sync, AI/RAG, or template editing.
- Do not create PDFs automatically from page load or from `/reports`.
- Keep report values backend-owned; frontend should only display backend responses.
