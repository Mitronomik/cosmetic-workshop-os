# Impeccable upstream review record and adapted guidance

This directory records the reviewed Impeccable source and contains a
project-authored, non-executable adaptation of selected UI principles.

Raw upstream command references are intentionally not included because they
contain executable workflows, missing cross-references, live-mode instructions,
and behavior that conflicts with this project's controlled Codex workflow.

It is stored outside `.agents/skills/` and is not an independently discoverable
or executable Codex skill.

## Provenance

- Repository: `pbakaus/impeccable`
- npm CLI package version reviewed: `3.2.1`
- Embedded upstream skill version: `3.9.1`
- Git commit: `0d1c34e9d0fcfff1070c7210cd808eda504105d7`
- License: Apache-2.0
- Upstream notice reviewed: `NOTICE.md`
- Notice decision: not vendored because its only attribution concerns the
  excluded upstream `ios.md` and `android.md` platform reference files, neither
  of which is included in or used as a source for `GUIDANCE.md`.

## Project restrictions

The following upstream content or capabilities are intentionally not
vendored or enabled:

- the upstream `SKILL.md`;
- raw upstream command reference files;
- executable scripts;
- hooks;
- live mode;
- automatic context loading;
- update checks;
- `impeccable init`;
- generation of `PRODUCT.md` or `DESIGN.md`;
- provider agents;
- automatic file mutation.

`GUIDANCE.md` is project-authored and contains only adapted advisory principles.

`GUIDANCE.md` is advisory only. Project architecture, product documentation,
UI/UX contract, repository AGENTS instructions, and the project-owned
`cosmetic-workshop-ui` skill always take priority.
