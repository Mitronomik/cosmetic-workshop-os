# Taste Skill review

## Decision

`senlindesign/taste-skill` was reviewed but is not approved for installation,
vendoring, source copying, or activation in `cosmetic-workshop-os`.

No upstream file is included in this repository. This document is a
project-authored review record.

## Reviewed upstream snapshot

- Repository: `senlindesign/taste-skill`
- Upstream commit: `6dce223f2f5665d3636ca9a44ec3a7aa1322a9b8`
- Declared skill version: `1.1.0`
- Review date: 2026-07-11
- Repository type: public, non-fork
- Tags: none at review time
- Releases: none at review time
- Upstream commit signature: unsigned
- Source archive SHA-256:
  `29f57f657b3eaa698291cbb7510e25fcc5aa2b65f458a2c8ee52b97000a23a4d`

Selected reviewed-file checksums:

- `SKILL.md`:
  `86baaf8bd95bbb7af5eed371c548f44d1ce4ff18c66e37ead9a350ffbbe1e597`
- `references/extract.js`:
  `b6387fbe746c9467da9dee317903a1eaa4516310c17e4da8d394d7eb2f8bce11`
- `references/step1-measure.md`:
  `a795bf08561649d35256245707298f385fb24013d52d37cb796d7410a6aca1de`
- `references/step2-pattern.md`:
  `67a6190a2ae548f9a4e4c56f51f451627f919d7ddd92b97c207f579ce5b6e293`
- `references/step3-taste.md`:
  `40417acab3c2bfe5803b6471ccec1abf98f8580395a7b3d1d29a8daf5a85787b`
- `references/step4-observer.md`:
  `f9fc3eb4f1ae41d6be4c2c3d0318efa34f116d106d921a9cdc0a1b5f5259e6c8`

## Material reviewed

The audit covered:

- repository metadata and the pinned source archive;
- `SKILL.md`;
- `README.md`;
- `evals/evals.json`;
- `references/extract.js`;
- the four analysis-stage Markdown references;
- export-format instructions;
- file permissions and executable-file candidates;
- static indicators of network, browser, filesystem, dependency, hook,
  agent, and project-mutation behavior;
- the complete available Git history for license and notice files.

Upstream source was inspected statically. It was not executed.

## Licensing finding

The README displays an MIT badge and contains an `MIT © 2025 Sen Lin`
statement. However:

- the referenced `LICENSE` file does not exist;
- there is no `LICENSE`, `LICENCE`, `COPYING`, or `NOTICE` file at the
  pinned commit;
- no such legal file exists in any reviewed commit;
- GitHub's license endpoint returns no detected license;
- no license-related issue or pull request existed at review time.

Under the project third-party policy, a badge or short README declaration
without the actual license terms is insufficient evidence for vendoring or
copying source material.

## Technical behavior observed

The upstream workflow is not passive guidance. It is designed to:

- require Playwright MCP and recommend an unpinned `@latest` package;
- download and use a browser runtime;
- navigate to external websites;
- take screenshots;
- execute a DOM and computed-style extractor inside the visited page;
- inspect up to thousands of rendered DOM elements;
- optionally crawl additional pages;
- write `{domain}.md` and `{domain}.json` into the current working directory;
- overwrite an existing analysis for the same domain;
- optionally append to or create tool instruction files;
- optionally overwrite `.bolt/prompt`;
- activate from broad natural-language design requests, not only from an
  explicit command.

`references/extract.js` itself did not contain direct shell execution,
child-process creation, or filesystem-writing APIs in the reviewed
snapshot. It is nevertheless executable browser-context JavaScript and is
part of a networked browser-automation workflow.

## Project-fit assessment

Installing the skill would create several conflicts with the project
contract:

- MVP work must remain focused on the local-first cosmetic workshop product;
- third-party automation must not introduce hidden runtime downloads;
- Codex Web must not execute unreviewed installers or browser tooling;
- canonical project instructions must not be appended to or overwritten by
  an external export workflow;
- outside design systems must not silently replace the approved visual
  identity of «Мастерская косметолога»;
- design work must remain understandable and scoped rather than becoming an
  automatic redesign pipeline;
- external-site capture introduces privacy, security, provenance, and
  imitation risks that are unnecessary for the MVP.

## Safe project-owned alternative

The useful general idea is evidence-based visual review:

1. separate measurable observations from interpretation;
2. cite concrete UI evidence;
3. identify repeated patterns;
4. explain trade-offs and rejected alternatives;
5. reject vague design language;
6. preserve the project's existing identity and architecture constraints.

These principles may be implemented independently in the project-owned
`cosmetic-workshop-ui` skill or in a future audit checklist. Any such work
must be written from scratch and must not copy upstream wording, prompts,
schemas, or JavaScript.

## Reconsideration requirements

Taste Skill may be reviewed again only when all of the following are true:

- the upstream repository contains complete, explicit license terms;
- the exact reviewed version or commit is pinned;
- browser and MCP dependencies are pinned and separately approved;
- invocation is explicit-only;
- all generated output is sandboxed outside canonical project files;
- no workflow can append to or overwrite `AGENTS.md`, tool instructions,
  configuration, product documentation, or application code;
- the security, legal, privacy, architecture, and product-identity review is
  repeated in a separate PR.
