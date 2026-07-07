# Handoff

## Last completed work

PR92 follow-up — deterministic PDF availability and report-document docs fix.

## What changed

- PDF tests no longer depend on host system fonts: PDF happy-path coverage monkeypatches PDF availability and writes fake PDF bytes.
- Backend status always includes Markdown and advertises PDF only when a local `.ttf` font exists, is parseable by the current renderer, and contains glyphs for a Russian sample string.
- TTC font collections (`.ttc`) are not treated as supported in PR92.
- `format: "pdf"` is rejected safely when PDF is unavailable.
- Pair-safety, rollback, no-overwrite behavior, no business-data mutation, no backup/export snapshot creation, and no alert/purchase regeneration remain covered.
- `docs/report-documents.md` no longer says PDF is future-only after PR92 and now describes “document file + metadata sidecar” wording.

## Manual smoke

Manual browser/PDF smoke was not run in this non-interactive environment. TestClient/httpx-dependent API tests are skipped in this environment when FastAPI TestClient dependencies are unavailable.

Recommended local smoke:
1. Start backend with a test user-data directory.
2. Open `/report-documents`.
3. Confirm available formats match backend status.
4. If PDF is unavailable, confirm only Markdown action is shown and PDF action is hidden.
5. If PDF is available, click «Создать PDF», confirm one `.pdf` and one `.json` sidecar appear in `exports/report-documents`, then open the PDF and confirm Russian text is readable.
6. Confirm `/reports` button only navigates to `/report-documents`.
7. Confirm no business rows, backups, JSON exports, alerts, purchase suggestions, production batches, imports, or demo data are created.

## Next recommended PR

PR93 — Report PDF UI polish / download-open workflow, unless smoke finds issues. If smoke finds issues, use PR93 for focused PDF generation follow-up fixes.
