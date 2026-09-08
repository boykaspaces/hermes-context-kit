# TASK-009: Add Installation and Adoption Gates to the Rollout

Status: Completed
Priority: High

## Goal

Correct the accepted AI delivery-governance rollout so that source design,
toolset installability, existing-project adoption, multi-repository
acceptance, and live runtime installation are validated as separate delivery
increments.

## Acceptance Criteria

- AC-1: The rollout includes an isolated toolset packaging and installation
  increment with clean-install, upgrade, inventory, rollback, and recovery
  checks.
- AC-2: An existing project adopts and exercises the capability through its
  own Task and pull request.
- AC-3: Multi-repository source acceptance, component locking, integration
  verification, and deployment remain separate facts.
- AC-4: Live Hermes installation uses the approved operator boundary and
  records readiness and rollback evidence separately from source acceptance.
- AC-5: Every added increment retains the review-and-merge stop gate.

## Capability Audit

Applicability: Not Required

This Task changes only the non-normative rollout plan and project-maintenance
state. It introduces no platform guarantee or executable mechanism.

## Completed

- Added an installable-toolset candidate increment.
- Added an existing-project adoption pilot increment.
- Added separate multi-repository acceptance and live Hermes installation
  increments.
- Moved the Phase 1 evidence decision after installation and consumer evidence.
- Preserved one Task and one pull request per increment.

## Remaining

None.

## Blockers

None.

## Out of Scope

- Implementing the advisory manual contract.
- Packaging or installing a delivery-governance Skill.
- Modifying a consuming project, component lock, deployment binding, or live
  Hermes runtime.
- Changing core Skills, schemas, CLI behavior, runtime adapters, or CI.

## Required Validation

- `./scripts/validate.sh`

## Relevant Files

- `docs/DELIVERY_GOVERNANCE_ROLLOUT.md`
- `tasks/README.md`
- `.context-kit/state.md`

## Result

The rollout now covers the complete source-to-runtime delivery path without
collapsing its independent acceptance boundaries.

## Next Step

None for TASK-009. After this proposal is accepted, create a new Task for the
advisory manual contract described as Increment 2 in the rollout plan.

