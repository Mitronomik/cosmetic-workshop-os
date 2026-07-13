# Current focus

## Active focus

Slice A1 — User-facing technical copy cleanup.

## Current repository state

PR #106 is already merged and verified. The verified PR #106 Hermes browser smoke covered Import Apply, refresh-failure separation, structured mutation conflict, Settings save/cancel behavior, scoped announcers, responsive behavior, and keyboard reachability.

This documentation-only implementation-plan PR only adds and links the approved MVP product-readiness plan. It does not implement Slice A1 and must not change frontend runtime code, backend runtime code, CSS, APIs, schemas, migrations, dependencies, or lockfiles.

## Next runtime PR

Slice A1 must be created as a separate focused runtime PR after this documentation-only PR. No future PR number has been assigned.

Allowed next-runtime focus for Slice A1:
- remove constant normal-state technical API availability copy;
- keep clear recovery copy when the local app is unavailable;
- remove PR/roadmap/internal planning language from runtime UI;
- fix stale Import copy around the actual Apply flow;
- translate internal table names on `/demo-data`;
- fix stale route/navigation readiness metadata;
- synchronize directly affected user/help documentation.

Non-goals for Slice A1:
- backend behavior changes;
- new product features;
- dashboard redesign;
- polling;
- arbitrary file browser;
- broad frontend refactor;
- validation-error migration;
- responsive table containment;
- tax/margin, restore, packaging, cloud, OCR, AI/RAG, roles, or multi-user behavior.
