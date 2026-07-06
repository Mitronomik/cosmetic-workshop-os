# Current focus

PR90 is implemented: frontend report document export UI plus the PR89 metadata sidecar cleanup hardening.

Next recommended PR: **PR91 — Report PDF generation foundation**, unless browser smoke or release testing finds issues in the new report document UI. If smoke finds issues, prefer **PR91 — Report document export UI follow-up fixes** before adding PDF.

Scope guard for the next session:
- Do not add PDF/DOCX unless the next task explicitly selects the PDF foundation.
- Do not add download/open-file endpoints, automatic generation, scheduled jobs, cloud sync, AI/RAG, or document template editing without explicit scope.
- Keep report values backend-owned; frontend should only display backend responses.
