# TASK-012: Validate GitHub Review Evidence Semantics

Status: Completed
Governance: Required
Priority: High

## Goal

Dogfood Capability Gate 0 against the real GitHub workflow boundary and
correct the advisory governance contract so exact revision binding, evidence
mutability, review independence, stale-review handling, and administrative
bypass are reported truthfully.

## Acceptance Criteria

- AC-1: The GitHub adapter states how pull-request heads and check runs bind
  validation to an exact commit SHA.
- AC-2: Pull-request comments are classified as mutable review records rather
  than immutable or independently trusted evidence.
- AC-3: Stale-review dismissal and required approval are described as
  repository-policy-dependent and do not conceal configured bypass actors.
- AC-4: Advisory Final Audit distinguishes exact target identity, evidence
  retention/mutability, reviewer independence, and workflow enforcement.
- AC-5: The late discovery from TASK-011 is recorded as a Capability Miss,
  while accepted historical evidence is not rewritten.
- AC-6: Repository validation passes and no schema, CLI, CI, runtime,
  installation, consumer, integration, or deployment behavior changes.

## Supported Scope

- The public `boykaspaces/hermes-context-kit` repository.
- GitHub pull requests, reviews, issue comments, Rulesets, and check runs.
- Read-only API observations and public GitHub documentation current for this
  audit.
- Advisory reporting, not a claim of tamper-proof audit storage.

## Out of Scope

- Removing or changing repository bypass actors or Rulesets.
- Adding a required Final Audit status check or GitHub App.
- Cryptographic attestation, external audit storage, or retention guarantees.
- Proving reviewer independence for the current account and workflow.
- Any runtime, consumer, component-lock, integration, or deployment change.

## Capability Audit

Applicability: Required
Gate Result: Pass
Matrix: `tasks/evidence/TASK-012/capability.md`

The contract is reduced to truthful advisory evidence: GitHub identifies exact
heads and check-run targets, but comments remain mutable and configured bypass
actors prevent a universal claim that review policy cannot be bypassed.

## Required Validation

- `./scripts/validate.sh`
- Exact-head comparison between PR #10 and its three check runs.
- Current `protect-main` Ruleset inspection.
- Manual contract audit against public GitHub semantics.

## Review

Ledger: `tasks/evidence/TASK-012/review.md`

## Completed

- Closed Capability Gate 0 against the live GitHub repository boundary.
- Identified one late Capability Miss from TASK-011.
- Corrected the advisory evidence language to separate exact identity,
  mutability, independence, enforcement, and bypass.
- Added the GitHub adapter's delivery-governance evidence mapping.
- Completed Initial Audit with one P1 matrix-enum finding and one P3 formatting
  finding.
- Resolved R-001 and R-002 without expanding the reviewed implementation.
- Delta Review verified both findings without a regression.
- Passed the complete repository validation after the reviewed fixes.
- Prepared an exact-head Final Audit record with explicit mutability,
  independence, enforcement, and bypass boundaries.

## Remaining

None.

## Blockers

None.

## Result

The GitHub platform audit preserved exact PR-head and check-run SHA binding but
removed stronger unsupported claims. Pull-request comments are now classified
as mutable advisory records, review enforcement is repository-policy-specific,
and configured bypass and reviewer independence are reported separately. One
Capability Miss, one P1 finding, and one P3 finding were recorded without
rewriting accepted historical evidence.

## Relevant Files

- `docs/experiments/DELIVERY_GOVERNANCE_V1.md`
- `docs/experiments/templates/review-ledger.md`
- `adapters/workflow/github/README.md`
- `tasks/evidence/TASK-012/capability.md`
- `tasks/evidence/TASK-012/review.md`

## Next Step

None for TASK-012. After this proposal is accepted, create a new Task for the
installable toolset candidate described as Increment 5 in the rollout plan.
