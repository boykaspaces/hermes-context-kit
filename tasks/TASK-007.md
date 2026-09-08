# TASK-007: Make Hermes Runtime Installation Transactional

Status: Completed
Priority: High

## Goal

Make Hermes adapter installation executable and truthful against the current
Hermes runtime: separate runtime files from source-only validation files,
produce Hermes-compatible discovery metadata, and prevent a partial multi-Skill
upgrade from being reported ready.

## Completed

- Reproduced the `tests/` versus `skill_manage` path conflict.
- Confirmed the 20-operation Hermes batch limit and lack of a trusted
  checkout-to-runtime import operation.
- Confirmed that Hermes does not route tags or related Skills from
  `metadata.context-kit`.
- Approved the bounded Hermes adapter v3 maintenance patch.
- Separated runtime and source-validation inventories so source tests never
  enter the Hermes Skill root.
- Made the current complete release route operator-only and documented
  `skill_manage` as unsupported for package installation.
- Added package staging, `ready`/`failed` state, complete verification, and
  explicit rollback for ordinary failures and interrupted transactions.
- Rendered Hermes-compatible discovery fields from portable Context Kit
  metadata without changing common Skill sources.
- Assigned installation source to `/workspace/.context-kit/sources/` and kept
  `/workspace/projects/` for deliberately managed projects.
- Added fresh, identical, different, interruption, rollback, legacy-manifest,
  metadata, and source-boundary coverage.
- Passed the complete repository validation suite.

## Remaining

None.

## Blockers

None.

## Relevant Files

- `adapters/runtime/hermes/runtime-contract.json`
- `adapters/runtime/hermes/scripts/runtime_setup.py`
- `adapters/runtime/hermes/README.md`
- `tests/test_hermes_runtime_setup.py`
- `docs/decisions/ADR-004-hermes-runtime-package-installation.md`

## Related Decisions

- ADR-003
- ADR-004

## Next Step

Publish the Context Kit 0.5.0 candidate, then let each consumer independently
accept the reviewed revision. Hermes host installation remains a separate
operator action and must not be inferred from source acceptance.
