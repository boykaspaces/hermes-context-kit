# Checkpoint

Project: hermes-context-kit
Task: TASK-005
Status: Archived
Created: 2026-09-08

## Objective

Implement the approved neutral-core, runtime-adapter, and merge-activation
architecture in Context Kit before changing consumer repositories.

## Completed

- Published project specification v2 and migrated Context Kit's own state from
  `.hermes/` to `.context-kit/`.
- Added Hermes and Codex runtime adapters and the GitHub workflow adapter.
- Classified Hermes `SOUL.md` as an operator-owned adapter template rather than
  a core or project artifact.
- Added guarded bootstrap and v1 migration behavior with clean-room,
  compatibility, conflict, path-safety, and rollback tests.
- Updated the project-context, multi-repository, and Skill-authoring Skills to
  the neutral contract and portable frontmatter.
- Completed all repository and standard Skill validation.

## Remaining

None for TASK-005.

## Blockers

None.

## Relevant Decisions

- ADR-002

## Resume Hint

Consumer rollout is new scope. Create a System Task, select each consumer's
runtime/workflow adapters explicitly, and validate the accepted component refs.
