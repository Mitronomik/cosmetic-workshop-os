# Current Focus

PR79 — Import validation refinement and apply readiness contract is implemented in this branch.

Scope remains limited to import draft validation/readiness and UI display:

- import drafts expose `apply_readiness` for ready, ready_with_warnings, blocked, cancelled, and failed states;
- validation supports visible header alias, decimal comma, unit alias, date, email, ID, and target-specific numeric checks;
- `/imports` displays readiness and still has no apply/confirmation button;
- import rows still are not applied to business domain tables.

Next recommended PR after smoke confirms readiness is clear: PR80 — Import apply backend foundation.
