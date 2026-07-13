# Current focus

## Active task

Slice A1 — User-facing technical copy cleanup.

## Exact scope

- Remove the normal-state positive API/backend availability indicator from runtime UI.
- Keep concise Russian recovery copy and existing manual retry actions for failed data loads.
- Update `/imports` copy to describe file selection → draft creation → preview/validation → confirmation → Apply → working records.
- Map `/demo-data` visible counters from backend keys to Russian product labels with a safe generic fallback.
- Correct stale runtime route/capability copy only where current functionality already exists.
- Update implementation/state documentation for this active branch.

## Explicit non-goals

No backend changes, API/schema/migration changes, seed/demo behavior changes, Import mutation changes, validation-error migration, responsive table work, file-path presentation redesign, restore, polling, automatic retry, dashboard redesign, tax/margin, cloud, OCR, AI/RAG, roles, or multi-user behavior.

## Required checks

- Targeted source inventory before and after edits.
- `git diff --check`, changed-file/diff review, frontend build, backend pytest.
- Existing frontend tests if available.
- Browser smoke remains a merge gate. If browser automation is unavailable locally, external Hermes verification must complete it.

## PR numbering

No next or future PR number is assigned.
