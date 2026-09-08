# TASK-010: Define the Advisory Delivery Governance Contract

Status: Completed
Priority: High

## Goal

Enable an explicitly experimental, advisory delivery-governance extension for
this repository and define the minimum manual Task contract, capability audit,
review ledger, convergence, and readiness conventions without changing core
protocol or automation.

## Acceptance Criteria

- AC-1: The adoption manifest explicitly enables advisory delivery governance
  and points to one canonical experimental reference.
- AC-2: The reference defines opt-in Task applicability without changing the
  five Task statuses or retroactively enrolling existing Tasks.
- AC-3: Capability Gate 0 distinguishes Not Required, Pass, Blocked, and
  Incomplete and cannot treat an unresolved dependency as Pass.
- AC-4: Review and validation evidence is Task-linked and bound to exact
  candidate revisions before final readiness.
- AC-5: Candidate readiness remains separate from workflow acceptance and from
  multi-repository or deployment state.
- AC-6: The experiment adds no reusable Skill, schema, CLI, CI, runtime, or
  consumer-project behavior.

## Capability Audit

Applicability: Required
Gate Result: Pass

- Adoption extension: Supported by the TASK-008 temporary-project validation
  and the current manifest extension contract.
- Optional Task fields: Supported by the TASK-008 temporary active-Task
  validation and the existing five-status parser.
- Candidate/canonical separation: Supported by project specification v2 and
  the GitHub workflow adapter.

No required guarantee for this advisory documentation increment remains
Unknown.

## Completed

- Enabled the advisory extension in this repository's adoption manifest.
- Added one canonical experimental governance reference.
- Defined Task applicability, contract, Delivery Stage, Capability Gate 0,
  evidence, finding, ledger, convergence, and readiness rules.
- Kept Task, workflow, multi-repository, runtime, and deployment owners intact.
- Preserved later dogfood, packaging, installation, and consumer adoption as
  separate merge-gated Tasks.

## Remaining

None.

## Blockers

None.

## Out of Scope

- Modifying `project-context-management` or another reusable Skill.
- Adding machine-readable review schemas, governance commands, or CI gates.
- Packaging or installing the experiment into a runtime.
- Modifying a consumer project, component lock, deployment binding, or live
  environment.
- Claiming independent review without evidence.

## Required Validation

- `./scripts/validate.sh`

## Relevant Files

- `.context-kit/manifest.json`
- `docs/experiments/DELIVERY_GOVERNANCE_V1.md`
- `docs/DELIVERY_GOVERNANCE_ROLLOUT.md`
- `docs/README.md`
- `docs/FILE_MAP.md`
- `tasks/README.md`
- `.context-kit/state.md`

## Result

This repository now has an explicit advisory governance contract that can be
dogfooded manually without changing or overstating core protocol guarantees.

## Next Step

None for TASK-010. After this proposal is accepted, create a new Task for the
first manual dogfood cycle described as Increment 3 in the rollout plan.

