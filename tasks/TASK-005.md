# TASK-005: Separate the Neutral Core from Runtime Adapters

Status: Completed
Priority: High

## Goal

Remove Hermes-specific runtime assumptions from the portable Context Kit
contract, introduce explicit runtime and workflow adapters, and define merge as
the activation boundary for candidate project state so normal delivery does not
require a recursive post-merge pull request.

## Completed

- Diagnosed the missing proposal-versus-canonical state boundary from the
  four-repository rollout.
- Identified direct core dependencies on `SOUL.md`, `.hermes/`, `AGENTS.md`,
  and `metadata.hermes`.
- Approved an architecture with a neutral core, runtime adapters, workflow
  adapters, and a compatible migration path.
- Published project specification v2 under the neutral `.context-kit/`
  namespace with logical profile artifacts and an explicit v1 migration path.
- Defined proposal merge as the atomic activation boundary; a proposal may
  carry its own completed Task, indexes, locks, and validation evidence without
  requiring a recursive post-merge proposal.
- Added versioned Hermes and Codex runtime adapters plus a GitHub workflow
  adapter. Hermes `SOUL.md` material is an operator template and is never
  written into a consumer project by the core CLI.
- Updated schemas, profiles, templates, all three Skills, and repository state
  to the neutral contract.
- Added a validation guard that rejects legacy `.hermes/` paths from the core
  project scaffold.
- Added guarded init and migration behavior covering adapter selection,
  extension preservation, full checkpoint/memory copying, path safety,
  conflict detection, rollback, and legacy v1 diagnosis.
- Passed repository validation, 39 multi-repository tests, 20 CLI tests,
  Markdown link validation, portability checks, and the standard Skill quick
  validator for all three Skills.

## Remaining

None. Consumer migrations are separate System/Component Tasks and are not part
of this protocol implementation Task.

## Blockers

None.

## Relevant Files

- `spec/project/v2.md`
- `docs/decisions/ADR-002-neutral-core-and-adapters.md`
- `adapters/`
- `scripts/context_kit.py`
- `skills/project-context-management/`
- `skills/multi-repo-system-management/`
- `skills/skill-authoring/`

## Related Decisions

- ADR-002

## Next Step

None.

## Result

Context Kit 0.3.0 has a runtime-neutral project contract, explicit adapter
boundary, deterministic v1-to-v2 migration path, and a non-recursive proposal
completion model. The complete candidate state becomes canonical when its
accepted integration ref contains this change.
