# TASK-008: Validate AI Delivery Governance Feasibility

Status: Completed
Priority: High

## Goal

Prove the minimum feasibility of an optional AI delivery-governance experiment
and define a bounded, sequential rollout before changing the Context Kit
protocol or automation.

## Acceptance Criteria

- AC-1: The existing 0.5.0 validator accepts advisory manifest metadata and
  optional Task contract fields in a temporary repository-profile project.
- AC-2: The rollout preserves existing Task, workflow-adapter, multi-repository,
  and runtime ownership boundaries.
- AC-3: Gate 0, candidate acceptance, revision binding, risk acceptance, and
  deferred-finding semantics are corrected before dogfooding.
- AC-4: Each later increment is bounded by its own Task and pull request, with
  an explicit stop after review readiness.

## Capability Audit

Applicability: Required
Gate Result: Pass

- Manifest extension support: Supported by temporary initialization and
  validation.
- Optional Task field compatibility: Supported by temporary active-Task
  validation.
- Candidate/canonical separation: Supported by project specification v2 and
  the GitHub workflow adapter.
- Cross-repository state separation: Supported by multi-repository
  specification v2.

No required guarantee for this documentation-only increment remains Unknown.

## Completed

- Confirmed PR #6 merged Context Kit 0.5.0 to the accepted `main` baseline.
- Validated advisory manifest metadata and optional Task fields in a temporary
  project without modifying the validator.
- Recorded corrected experimental semantics and existing ownership boundaries.
- Split the rollout into independently reviewed increments.
- Reserved core Skill, schema, CLI, CI, runtime, and autonomy changes for later
  evidence-gated Tasks.

## Remaining

None.

## Blockers

None.

## Out of Scope

- Enabling delivery governance in the adoption manifest.
- Modifying reusable Skill behavior or maintenance policy.
- Adding review schemas, CLI commands, CI gates, or autonomous execution.
- Advancing any consuming repository's component lock or deployment binding.

## Required Validation

- Temporary repository-profile validation with advisory extension metadata and
  optional Task contract fields: Passed.
- `./scripts/validate.sh`

## Relevant Files

- `docs/DELIVERY_GOVERNANCE_ROLLOUT.md`
- `docs/README.md`
- `docs/FILE_MAP.md`
- `tasks/README.md`
- `.context-kit/state.md`

## Result

The documentation-only advisory approach is feasible without changing the
stable Task status model or current schemas. The rollout is divided into
sequential, merge-gated Tasks.

## Next Step

None for TASK-008. After this proposal is accepted, create a new Task for the
advisory manual contract described as Increment 2 in the rollout plan.

