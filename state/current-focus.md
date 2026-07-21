# Current focus

Slice A5 is DONE. PR #131 merged at `62d372644d00fab38ccb1d652ab44556d8241b6a` (`Merge pull request #131 from Mitronomik/codex/implement-a5-local-artifact-presentation`).

## Active task

**Frontend focused-test infrastructure repair**

Repair the four focused frontend TypeScript test scripts so they compile only their intended source modules through repository-local TypeScript project configs, emit temporary JavaScript only under `frontend/dist-tests/`, clean stale suite output before each run, and then execute the existing Node `.mjs` tests.

## Diagnostic baseline

The B1/B2 diagnostic audit found no fixture/backend implementation defect requiring a correction PR. It confirmed explicit demo-data installation, safe duplicate-install rejection, stable alert regeneration, stable purchase-suggestion regeneration, meaningful operational source data, and no passive database mutations. No B1 backend/fixture correction and no B2 backend read-model correction is currently required.

B2 browser presentation was not fully verified by that diagnostic audit, so do not overstate browser evidence.

## Non-goals

Do not change runtime frontend behavior, user-visible copy, CSS, routes, API requests, backend code, tests, database schema, migrations, dependencies, demo data, alerts, purchase suggestions, Dashboard, onboarding, Help Center, or B3.1 runtime behavior. Do not fix the known backend baseline failures in this task.

## Next runtime slice

B3.1 — Shared feedback for Dashboard, Onboarding and Help.

No B1 or B2 implementation PR is active. Do not assign a future PR number before GitHub creates it.
