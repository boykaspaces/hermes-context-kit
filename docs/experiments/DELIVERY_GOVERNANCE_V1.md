# Advisory AI Delivery Governance v1

Status: Experimental
Mode: Advisory

## Purpose

Provide a small, inspectable manual contract for bounded implementation and
review. It supplements Context Kit project state without redefining Task
status, workflow acceptance, multi-repository delivery, runtime authority, or
deployment truth.

This experiment has no automatic enforcement. A Task or review record cannot
grant filesystem, Git, workflow, runtime, deployment, or risk-acceptance
authority that the underlying environment does not provide.

## Applicability

This reference applies only when both conditions are true:

1. `.context-kit/manifest.json` enables the `delivery-governance` extension.
2. The current Task declares `Governance: Required`.

Use `Governance: Not Required` for a persistent Task that does not need the
workflow. Existing Tasks without the field are not retroactively enrolled.
Trivial requests that do not justify a persistent Task remain outside this
experiment.

## Ownership Boundaries

- `project-context-management` owns Task identity, the five Task statuses,
  current pointers, progress, blockers, and completion.
- The configured workflow adapter owns proposal acceptance and activation of
  candidate state on the canonical ref.
- `multi-repo-system-management` owns component source, acceptance,
  integration, deployment, and rollback state across repositories.
- Runtime adapters and authoritative platform evidence own primitive and
  authority claims.
- This extension owns only the optional Task contract, capability-audit, and
  review-governance conventions defined here.

Governance evidence never advances a stronger owner automatically.

## Task Contract

A governed Task adds these fields or sections:

```markdown
Governance: Required

## Acceptance Criteria

- AC-1: <observable result or invariant>

## Out of Scope

- <explicitly excluded behavior>

## Capability Audit

Applicability: Required | Not Required
Gate Result: Not Required | Pass | Blocked | Incomplete
Matrix: tasks/evidence/TASK-NNN/capability.md

## Required Validation

- <repository-controlled validation name or manual Phase 1 command>

## Review

Ledger: tasks/evidence/TASK-NNN/review.md
Final Audit: External exact-head workflow evidence
```

Acceptance Criteria describe observable results. Out of Scope prevents a
reasonable future improvement from silently becoming current work. Required
Validation lists the deterministic evidence needed by this Task; it does not
grant permission to execute arbitrary commands.

The frozen contract consists of the Task Goal, Acceptance Criteria, Out of
Scope, supported scenarios, applicable specification and ADR rules, and
declared validation. A material contract change returns the Task to `Plan` and
invalidates review evidence based on the previous contract.

## Delivery Stage

`Delivery Stage` is optional secondary progress for a governed Task. It never
replaces Task `Status`.

Allowed values while a Task is `In Progress` or `Blocked` are:

```text
Plan
Build
Initial Audit
Fix
Delta Review
Stabilization
Validate
Final Audit
```

A Blocked Task retains the stage at which it became blocked; `Blockers` owns
the reason. Completed and Cancelled Tasks omit Delivery Stage.

`Ready for Acceptance` is a derived workflow condition, not a persisted
Delivery Stage. A candidate Task may contain `Status: Completed`; the workflow
adapter still owns whether that candidate has become canonical.

## Capability Gate 0

Use Capability Gate 0 before freezing the contract when correctness depends
materially on an external runtime, API, filesystem, cloud service, workflow,
package manager, or other platform primitive whose behavior is not already
supported by sufficient current evidence.

Each required guarantee records:

```text
ID
Guarantee
Required Primitive
Evidence
Failure Boundary
Result: Supported | Unsupported | Unknown
Disposition: Keep | Reduce Contract | Accept Risk | Add Dependency
```

Gate results mean:

| Gate Result | Meaning |
|---|---|
| `Not Required` | The Task has no material uncertain platform dependency |
| `Pass` | Every guarantee retained by the frozen contract is supported or covered by explicit authorized risk acceptance |
| `Blocked` | A required dependency or primitive is unavailable and the Task cannot progress |
| `Incomplete` | A required capability remains Unknown or the evidence cannot be obtained or verified |

`Add Dependency` does not produce `Pass` while that dependency remains
unresolved. `Accept Risk` records the approving authority, approval evidence,
known limitation, failure mode, recovery action, and reevaluation condition.
The matrix cannot approve its own exception.

Coordination metadata such as a journal, receipt, lock, ledger, result file, or
attestation may record an existing capability. It cannot manufacture missing
authority, atomicity, identity, observability, rollback, or recovery.

## Task-Linked Evidence

Phase 1 stores detailed evidence only when the Task needs it:

```text
tasks/evidence/TASK-NNN/
├── capability.md
└── review.md
```

The Task links each file directly. Do not create a global evidence index until
multiple artifacts make one useful. The Task remains the owner of Goal,
Status, progress, blockers, and Next Step; evidence files do not duplicate
that narrative state.

An evidence claim identifies a stable repository-relative file, immutable
revision, authoritative source, or durable external URL. A prose summary alone
does not prove a state transition. Never store credentials, tokens, private
keys, secret values, or authority-bearing material in evidence.

## Review Boundary

Review the candidate against the frozen Task contract, supported scenarios,
repository invariants, applicable specifications and ADRs, and declared
validation. Do not use an open-ended request for every imaginable improvement.

A finding blocks only when it demonstrates one of:

1. an explicit contract, specification, ADR, or repository-invariant
   violation;
2. incorrect behavior in a supported scenario;
3. a material safety, security, data-integrity, or false-readiness risk; or
4. a contradiction between canonical owners that makes behavior ambiguous or
   falsely reported.

Severity:

| Severity | Meaning | Blocks? |
|---|---|---|
| `P0` | Critical correctness, safety, data-loss, or false-state defect | Yes |
| `P1` | Material supported-scenario or contract defect | Yes |
| `P2` | Useful non-critical improvement | No by default |
| `P3` | Style, polish, or speculative future improvement | No |

Every finding receives exactly one disposition:

```text
FIX
REJECT
DEFER
DUPLICATE
```

`FIX` findings move `Open -> Resolved -> Verified`. `REJECT`, `DEFER`, and
`DUPLICATE` findings close without a fix. A deferred finding does not create a
Planned Task or expand scope unless the user or an explicit project policy
accepts it as new work.

## Review Ledger

The Phase 1 Markdown ledger records at least:

```text
Task
Contract Revision
Initial Audit Base Revision
Candidate Binding
Validation Target
Final Audit Evidence
Review Mode
Findings
Gate Summary
```

Each finding records ID, severity, origin, violated contract or evidence,
disposition, status, and observed candidate revision. Origin is `Baseline`,
`Late Discovery`, or `Regression`; a Regression also identifies the fix or
revision that introduced it.

Initial and Delta review may inspect declared dirty working state. An in-repo
ledger cannot embed the SHA of the commit containing that exact ledger content:
writing the SHA changes the tree and therefore the commit identity. The ledger
therefore records the configured candidate binding, while durable external
workflow evidence records the exact full pull-request head reviewed by Final
Audit.

Final Audit and readiness require that exact external head identity. No
candidate mutation is allowed after Final Audit. Any later push invalidates
affected validation, verified findings, and Final Audit. Re-run only the
evidence whose scope intersects the change, then review the new exact head. If
the workflow cannot expose an immutable candidate identity and durable review
evidence, readiness is `Incomplete` rather than assumed.

## Convergent Review Loop

1. `Initial Audit` produces one consolidated finding set against the frozen
   contract.
2. `Fix` changes only explicit criteria or `FIX` findings.
3. `Delta Review` verifies targeted fixes and regressions in their affected
   scope; it does not reopen unrestricted architecture review.
4. `Validate` runs the required deterministic gates.
5. `Final Audit` asks only whether the exact candidate still contains a P0 or
   P1 violation of the frozen supported contract.

Enter `Stabilization` before further patching when review is not converging,
including when two consecutive rounds add blocking Late Discoveries, blocking
findings do not decrease, several findings share one state or trust boundary,
or local fixes increase complexity without establishing a clear invariant.

Stabilization freezes the candidate and supported threat model, clusters root
causes, defines state/trust/recovery invariants, and builds an invariant test
matrix before implementation resumes. Semantic clustering remains a human or
AI judgment in Phase 1; it is not presented as a deterministic gate.

## Candidate Readiness

A governed candidate is ready for workflow acceptance only when:

```text
Goal satisfied
Acceptance Criteria satisfied
Remaining empty or explicitly outside scope
Blockers empty
Open P0/P1 findings = 0
Required validation passes for the exact workflow candidate revision
Final Audit passes for that exact revision in durable workflow evidence
```

The candidate may contain the complete `Status: Completed` transition and all
affected Task, state, and index updates. The configured workflow adapter
activates that candidate on the canonical ref. In multi-repository work, local
readiness never advances component, integration, lock, or deployment state
without the separate evidence required by `multi-repo-system-management`.

## Phase 1 Limits

This advisory version does not provide:

- a JSON ledger schema;
- a governance CLI or CI gate;
- automatic command execution;
- automatic Task selection or scope expansion;
- automatic merge, installation, or deployment;
- concurrent-writer coordination;
- proof that logically separate reviewer roles are independent.

Every rollout increment remains one bounded Task and pull request. Notify the
user when review is ready and stop until that pull request is accepted.
