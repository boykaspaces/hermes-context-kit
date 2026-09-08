# TASK-011: Dogfood the Advisory Governance Contract

Status: In Progress
Delivery Stage: Plan
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

## Remaining

- Add the two experimental evidence templates.
- Correct the advisory contract's Final Audit evidence boundary.
- Run Initial Audit, fix any blocking findings, and validate the candidate.
- Prepare the exact pull-request head for external Final Audit.

## Blockers

None.

## Relevant Files

- `docs/experiments/DELIVERY_GOVERNANCE_V1.md`
- `docs/experiments/templates/capability-audit.md`
- `docs/experiments/templates/review-ledger.md`
- `tasks/evidence/TASK-011/capability.md`
- `tasks/evidence/TASK-011/review.md`

## Next Step

Freeze this Task contract, then add the experimental evidence templates and
run Initial Audit against the resulting candidate.

