# Handoff

PR98 integrated editable Workshop profile settings with newly generated report documents and cleaned stale Settings/state copy.

Changed behavior:
- Newly generated Markdown `Сводка мастерской` documents include `Профиль мастерской` near the top when at least one profile field is configured.
- Newly generated PDF overview documents use the same backend-built presentation lines, so configured profile fields are included when local PDF support is available.
- Empty profile fields are omitted; an entirely empty/default profile omits the profile section and document generation still succeeds.
- Profile values are rendered as plain document text and escaped/neutralized for Markdown control characters and HTML-like text.
- Existing generated Markdown/PDF files and metadata sidecars are not mutated.
- `GET /api/settings/status` and `/settings` copy now say the Workshop profile is editable while calculation-sensitive settings remain out of scope.
- `/report-documents` explains that filled Workshop profile fields are added to new Markdown/PDF summaries.

Safety notes:
- Profile values are display metadata only and do not affect calculations.
- Report values still come from backend `ReportsService`; frontend does not inject profile values into generated documents.
- Document generation remains explicit and backend-owned.
- No recipes, clients, orders, production, stock, costs, taxes, margins, alerts, purchases, imports, exports, backups, demo data, or historical records are changed by this integration.
- No tax/currency/margin/unit settings, stock-threshold settings, expiry settings, template editor, logo upload, DOCX, invoices, labels, certificates, roles/auth, cloud sync, integrations, scheduled jobs, or AI/RAG were added.

Manual smoke was not run in a browser in this non-interactive environment. Recommended smoke: open `/settings`, save profile fields, open `/report-documents`, create/download Markdown, confirm only non-empty profile fields appear, create/open PDF if available, clear profile via API or UI, generate another document, and confirm no profile section/no crash and previous files remain unchanged.

Next recommended task: PR99 — Workshop profile display polish / app header integration, or PR99 — Workshop profile report document integration follow-up fixes if smoke finds issues.
