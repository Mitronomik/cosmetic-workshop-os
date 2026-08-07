# docs/decisions/AGENTS.md

Scope: architecture decision records under `docs/decisions/`.

ADR rules:

- ADRs document important architecture decisions and their reasoning.
- Do not rewrite accepted ADR history casually; preserve decision context for future maintainers.
- If a major decision changes, create a new ADR that supersedes or amends the older one.
- Each ADR should include status, context, decision, considered alternatives and consequences.
- Keep ADRs focused on one decision per file.
- Do not store secrets, credentials or real user data in ADRs.

Authority and lifecycle rules:

- Resolve ADR conflicts by **scope and recency**, not by assuming that every older accepted ADR outranks every newer lifecycle document.
- A newer accepted ADR may supersede only a bounded part of an older ADR while leaving the older durable decision semantics unchanged.
- ADR 0017 supersedes the dated C4 implementation-status and authorization wording in ADR 0016 after PR #170 merged.
- ADR 0016 remains authoritative for the launcher-assisted Restore product decision, twelve-phase state machine, transition graph, startup recovery matrix, `replacement_intent` rule, launcher ownership, immutable source, mandatory safety copy, and AuditLog boundary.
- For current C4 implementation lifecycle and authorization, read `docs/current-lifecycle.md` and ADR 0017 before acting on branch-era status tables in ADR 0016.
- A historical `NOT MERGED`, `NOT STARTED`, or old authorization label inside an earlier ADR cannot reopen completed work or authorize a later runtime slice.
- Do not start CR-011 from the unmerged PR #171 branch. CR-011 begins only from updated `main` after PR #171 merges.