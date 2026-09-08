# TASK-011: Dogfood the Advisory Governance Contract

Status: Completed
Governance: Required
Priority: High

## Goal

Exercise the advisory governance contract on one bounded repository change by
adding experimental Phase 1 evidence templates and resolving how an in-repo
ledger can truthfully bind final review to a Git candidate.

## Acceptance Criteria

- AC-1: Experimental capability-audit and review-ledger templates implement the
  fields and state semantics of the advisory contract without becoming core
  templates.
- AC-2: The self-reference limitation of embedding a containing commit SHA in
  an in-repo ledger is explicitly dispositioned before implementation.
- AC-3: Final Audit targets an exact pull-request head through external
  workflow evidence, and any later candidate change invalidates that audit.
- AC-4: Task-linked evidence records the frozen contract, Initial Audit,
  findings, validation, and final review boundary without duplicating Task
  progress truth.
- AC-5: Repository validation passes and no core Skill, schema, CLI, CI,
  runtime, consumer, integration, or deployment behavior changes.

## Supported Scope

- Markdown-only experimental evidence templates.
- Git-backed projects using a workflow adapter that can expose an immutable
  candidate revision and durable review evidence.
- One writer and one pull-request candidate for this Task.

## Out of Scope

- Machine-readable ledgers or automated governance checks.
- Adding templates to the released runtime package.
- Proving reviewer independence.
- Consumer adoption, component-lock advancement, runtime installation, or
  deployment.
- Concurrent candidate writers or non-Git workflow semantics.

## Capability Audit

Applicability: Required
Gate Result: Pass
Matrix: `tasks/evidence/TASK-011/capability.md`

The original in-repository final-SHA requirement is unsupported. The contract
is reduced to external workflow evidence that binds Final Audit to the exact
pull-request head and permits no later candidate mutation.

## Required Validation

- `./scripts/validate.sh`
- Markdown link validation through the repository validator.
- Manual contract audit against the exact Task scope.

## Review

Ledger: `tasks/evidence/TASK-011/review.md`

## Completed

- Closed Capability Gate 0 and dispositioned the final-SHA self-reference
  limitation.
- Added experimental capability-audit and review-ledger templates.
- Corrected the advisory contract to use external exact-head Final Audit
  evidence.
- Completed Initial Audit with no P0/P1 findings and one P3 formatting finding.
- Resolved the tracked trailing-blank-line finding.
- Delta Review verified R-001 without a regression.
- Passed the complete repository validation after the reviewed fix.
- Prepared Final Audit as external workflow evidence against the exact
  pull-request head.

## Remaining

None.

## Blockers

None.

## Result

The first manual dogfood cycle produced two reusable experimental evidence
templates and corrected an unsupported self-referential revision rule. Initial
Audit found no blockers, Delta Review verified the only P3 fix, and final
readiness is intentionally left to exact-head workflow evidence and user
review.

## Relevant Files

- `docs/experiments/DELIVERY_GOVERNANCE_V1.md`
- `docs/experiments/templates/capability-audit.md`
- `docs/experiments/templates/review-ledger.md`
- `tasks/evidence/TASK-011/capability.md`
- `tasks/evidence/TASK-011/review.md`

## Next Step

None for TASK-011. After this proposal is accepted, create a new Task for the
platform-dependent dogfood cycle described as Increment 4 in the rollout plan.
