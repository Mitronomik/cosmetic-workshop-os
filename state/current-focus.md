# Current focus — B4.1 Safe GET timeout and recovery foundation

Status: `ACTIVE NEXT RUNTIME SLICE` — documented here, not yet implemented. No future PR number is assigned.

## Goal

Introduce a bounded timeout and recovery contract for explicitly selected safe frontend GET/read operations without changing backend business rules and without introducing mutation retries.

## Allowed scope

Use the existing Dashboard read lifecycle as the only initial pilot:

- Dashboard initial read;
- Dashboard manual refresh;
- a bounded timeout policy selected, documented, and tested by the runtime PR;
- clear Russian user-facing timeout feedback;
- explicit manual retry or refresh;
- preservation of the last valid Dashboard snapshot after a timed-out refresh where safe;
- rejection of stale or late results;
- route/context ownership for accepted results, feedback, announcements, and focus;
- an opt-in safe-GET transport boundary limited to the pilot if transport support is required.

Reuse and extend the existing `DashboardOnboardingFeedbackLifecycle` and current API client boundary. Do not create a second Dashboard lifecycle system or authorize a global fetch rewrite.

## Expected affected area

The later runtime PR is expected to stay within the smallest relevant Dashboard/frontend surface:

- `frontend/src/dashboard-onboarding-feedback.ts`;
- Dashboard read composition in `frontend/src/main.ts`;
- existing centralized frontend API request code only if an explicitly opt-in safe-GET timeout primitive is required;
- focused Dashboard lifecycle tests and directly relevant frontend regression tests;
- minimal state/documentation updates.

The runtime task must inspect the final baseline before naming its exact changed-file list.

## Non-goals

Do not include:

- backend runtime, API contract, schema, migration, or business-rule changes;
- automatic retry for `POST`, `PUT`, `PATCH`, or `DELETE`;
- automatic retry for production, Import Apply, stock movement creation, backup creation, export creation, report generation, or any other mutation;
- onboarding, Alerts, Purchases, production, imports, backups, exports, reports, or other mutation-flow migration;
- hidden polling, health polling, background refresh loops, offline synchronization, or cloud sync;
- a global frontend request rewrite;
- a framework migration or new dependency;
- calculations, tax, margin, restore, AuditLog UI, packaging, update installation, OCR, AI/RAG, roles, or multi-user behavior;
- correction of the four known backend baseline failures.

## Architecture constraints

- Preserve local-first operation and the existing API-first boundary.
- Keep backend-owned calculations, production, imports, stock writes, migrations, and business rules unchanged.
- Treat timeout as a safe-read transport outcome, not as permission to repeat a mutation.
- Make the timeout policy explicit in the runtime PR; this documentation does not choose an exact duration.
- Accept a result only when its request identity and current Dashboard route/context ownership are still valid.
- A timed-out, superseded, detached, or late result must not overwrite a newer accepted result or present stale feedback.
- Preserve the last valid readable Dashboard snapshot after refresh timeout where safe and label it as potentially stale.
- Recovery must be explicit and user-triggered.
- Keep user-facing feedback Russian, human-readable, actionable, keyboard reachable, and free of technical exception details.
- Preserve immutable history, versioned recipes, first-class client recipes, lot/movement inventory, transactional production, import confirmation, and backup-before-migration rules.

## Required tests

The later runtime PR must add or update focused tests for:

- the selected timeout policy and its exact boundary;
- initial Dashboard read timeout with no prior snapshot;
- manual Dashboard refresh timeout while preserving the last valid snapshot;
- explicit manual retry succeeding after timeout;
- no automatic retry after timeout;
- late success and late failure rejection after timeout;
- stale result rejection after a newer request or route/context change;
- duplicate-request protection and final busy-state release;
- route-owned feedback, announcement, and focus behavior;
- proof that mutation request paths are not wrapped or retried by the safe-GET timeout behavior;
- existing Dashboard/Onboarding lifecycle regressions and frontend production build.

No backend test change is expected unless later inspection finds an independently justified backend defect, which would require a separate task.

## Browser smoke requirements

Run exact-head browser smoke for the Dashboard pilot with isolated local data:

- desktop and narrow viewport;
- keyboard access and visible focus for refresh/retry;
- normal initial load;
- intentionally delayed initial GET beyond the selected timeout;
- successful manual recovery;
- timed-out manual refresh preserving the last valid snapshot with clear stale-data feedback;
- a late response that cannot overwrite a newer accepted Dashboard state;
- route leave/return ownership;
- no hidden polling or automatic retry;
- no unexpected console errors, HTTP failures, or request failures outside intentional fault injection.

The documentation-only lifecycle PR that activated this slice does not claim or require this future runtime smoke.

## Acceptance criteria

- Only the bounded Dashboard safe-read pilot is implemented.
- The runtime PR explicitly documents and tests its timeout duration/policy.
- Timeout feedback is clear, Russian, and offers manual recovery.
- The last valid Dashboard snapshot remains readable after refresh timeout where safe.
- Late, stale, detached, and wrong-context responses cannot present or overwrite state.
- Manual retry/refresh is the only retry path.
- No mutation is automatically retried.
- No polling, cloud dependency, framework migration, backend behavior change, API change, schema change, migration, or unrelated route rewrite is introduced.
- Focused tests, required regressions, frontend build, and exact-head Dashboard browser smoke pass.
