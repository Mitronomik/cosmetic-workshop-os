# Third-Party Codex Skills Registry

This registry tracks third-party Codex skills that may be considered for **cosmetic-workshop-os**. It is a documentation template and planning record only. Third-party skill content is not copied into the repository by this file.

Before any third-party skill is installed or vendored, a separate PR must review source, license, scripts, hooks, invocation behavior, and compatibility with `docs/ui-skill-policy.md` and `docs/ui-ux-contract.md`.

## Required registry fields for every future skill

- Skill name
- Purpose
- Source repository
- Imported version or commit SHA
- Import date
- License
- Included scripts
- Included hooks
- Reviewed files
- Local modifications
- Implicit invocation policy
- Approved use cases
- Forbidden use cases
- Update policy

## Planned entries

### Impeccable

- Status: not installed
- Skill name: Impeccable
- Purpose: UI audit, hierarchy, layout, typography, accessibility, responsive behavior, hardening, and final polish.
- Source repository: TBD
- Imported version or commit SHA: not imported
- Import date: not imported
- License: TBD before installation
- Included scripts: none installed
- Included hooks: none installed
- Reviewed files: none yet
- Local modifications: none
- Implicit invocation policy: TBD; must remain subordinate to project documentation and explicit task scope.
- Approved use cases: future evidence-based UI audits and polish of approved routes.
- Forbidden use cases: changing architecture, domain logic, APIs, schemas, migrations, dependencies, unrelated routes, historical/operational data, or product identity.
- Update policy: install/update only in explicit separate PR with review.

### Taste Skill

- Status: not installed
- Skill name: Taste Skill
- Purpose: explicit-only critique or redesign exploration.
- Source repository: TBD
- Imported version or commit SHA: not imported
- Import date: not imported
- License: TBD before installation
- Included scripts: none installed
- Included hooks: none installed
- Reviewed files: none yet
- Local modifications: none
- Implicit invocation policy: none unless explicitly requested by a task.
- Approved use cases: future design critique or exploratory redesign reports when explicitly scoped.
- Forbidden use cases: automatic redesign, replacing the approved product identity, changing unrelated routes, adding dependencies, or altering product/domain/architecture contracts.
- Update policy: install/update only in explicit separate PR with review.

### Emil design skills

- Status: not installed
- Skill name: Emil design skills
- Purpose: motion design support after layout and interaction states are approved.
- Source repository: TBD
- Imported version or commit SHA: not imported
- Import date: not imported
- License: TBD before installation
- Included scripts: none installed
- Included hooks: none installed
- Reviewed files: none yet
- Local modifications: none
- Implicit invocation policy: none unless explicitly requested by a motion task.
- Approved use cases: future limited, purposeful motion work with reduced-motion support after UI states are approved.
- Forbidden use cases: layout redesign before approval, decorative animation on operational screens, ignoring reduced motion, dependency additions without approval, or changes to domain/API/schema behavior.
- Update policy: install/update only in explicit separate PR with review.
