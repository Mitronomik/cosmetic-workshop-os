# Current focus

PR90 is implemented: frontend report document export UI plus the PR89 metadata sidecar cleanup hardening.

The next implementation PR should be **Report PDF generation foundation**, unless PR90 browser smoke or release testing finds issues in the new report document UI. If smoke finds issues, the next implementation PR should fix the report document UI before PDF.

Scope guard for the next session:
- Do not add PDF/DOCX unless the next task explicitly selects the PDF foundation.
- Keep download/open-file endpoints, automatic generation, scheduled jobs, cloud sync, AI/RAG, document template editing, and document preview out of scope unless explicitly requested.
- Keep report values backend-owned; frontend should only display backend responses.
