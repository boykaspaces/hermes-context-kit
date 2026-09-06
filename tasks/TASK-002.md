# TASK-002: Support Unchanged-Component Promotion

Status: Completed
Type: Component
Priority: High
Parent System Task: personal-hermes-agent:TASK-012

## Goal

Allow a System Task to merge, lock, or deploy an unchanged component revision
without creating a fictitious Component Task, while retaining a stable pointer
to the System Task that originally delivered it.

## Completed

- Added the `no-component-change` absence reason.
- Required a canonical `source_system_task` for unchanged revisions.
- Added a positive and negative validator test.

## Remaining

None.

## Blockers

None.

## Relevant Files

- `skills/multi-repo-system-management/references/tasks-and-delivery.md`
- `skills/multi-repo-system-management/references/validation.md`
- `skills/multi-repo-system-management/scripts/validate_multi_repo_context.py`
- `skills/multi-repo-system-management/tests/test_validate_multi_repo_context.py`

## Next Step

None. Use `no-component-change` only when an earlier System Task supplies the
unchanged revision.

## Result

Unchanged-component promotion is validated without creating false component
work, and missing `source_system_task` is rejected.
