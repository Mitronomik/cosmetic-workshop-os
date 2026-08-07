# docs/decisions/AGENTS.md

Scope: architecture decision records under `docs/decisions/`.

ADR rules:

- ADRs document important architecture decisions and their reasoning.
- Do not rewrite accepted ADR history casually; preserve decision context for
  future maintainers.
- If a major decision changes, create a new ADR that supersedes or amends the
  older one.
- Each ADR should include status, context, decision, considered alternatives and
  consequences.
- Keep ADRs focused on one decision per file.
- Do not store secrets, credentials or real user data in ADRs.

Authority and lifecycle rules:

- Resolve ADR conflicts by **scope and recency**, not by assuming that every older
  accepted ADR outranks every newer lifecycle document.
- A newer accepted ADR may supersede only a bounded part of an older ADR while
  leaving older durable semantics unchanged.
- ADR 0016 remains authoritative for the launcher-assisted Restore product
  decision, twelve-phase state machine, transition graph, startup recovery
  matrix, `replacement_intent`, destructive launcher ownership, immutable
  source, mandatory safety copy and AuditLog boundary.
- ADR 0017 supersedes the dated C4 implementation-status and authorization
  wording in ADR 0016 after PR #170 merged. It remains authoritative for C4-I
  lifecycle closure and for the rule that CR-011 was a decision-only gate rather
  than runtime authorization.
- ADR 0018 is newer for the exact CR-011 interaction/validation-session topic. It
  supersedes ADR 0017 **only** where ADR 0017 says CR-011 is still undecided or
  C4-II-A is still blocked by that undecided decision gate.
- ADR 0018 selects the launcher-owned loopback control plane, launcher-owned macOS
  picker, exact-run browser security model and non-destructive validation-session
  contract.
- ADR 0018 does **not** amend ADR 0016's durable Restore state machine or safety
  semantics and does **not** authorize C4-II-A runtime implementation by itself.
- For current C4 lifecycle and runtime authorization, read
  `docs/current-lifecycle.md` before acting on branch-era status tables in older
  ADRs.
- A historical `NOT MERGED`, `NOT STARTED`, `NOT DECIDED`, `BLOCKED BY CR-011`,
  or old authorization label cannot reopen completed work or authorize a later
  runtime slice.
- Decision ADRs carried on a PR branch become normative project authority only
  when the changeset is present on `main`; do not start successor runtime work
  from an unmerged architecture-decision branch.