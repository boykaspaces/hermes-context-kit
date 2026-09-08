# Review Ledger — TASK-{{task_id}}

Task: TASK-{{task_id}}
Contract Revision: {{full commit SHA containing the frozen Task contract}}
Initial Audit Base Revision: {{full commit SHA or declared dirty state}}
Candidate Binding: {{configured workflow proposal head}}
Validation Target: {{exact full candidate SHA recorded by workflow evidence}}
Final Audit Evidence: {{durable external review/check URL or Pending}}
Review Mode: Not Started

## Supported Review Scope

- {{Task acceptance criteria}}
- {{supported scenarios}}
- {{applicable specification, ADR, and repository invariants}}

## Findings

| ID | Severity | Origin | Contract / Evidence | Observed Revision | Disposition | Status | Introduced By |
|---|---|---|---|---|---|---|---|
| R-001 | P0 / P1 / P2 / P3 | Baseline / Late Discovery / Regression | {{AC, invariant, or evidence}} | {{full SHA or declared dirty state}} | FIX / REJECT / DEFER / DUPLICATE | Open / Resolved / Verified / Closed | {{finding/fix/SHA or Not Applicable}} |

Delete the example row when there are no findings. `FIX` follows
`Open -> Resolved -> Verified`; other dispositions end at `Closed`.

## Review Rounds

| Round | Mode | Target | New Blocking | Closed Blocking | Result |
|---|---|---|---:|---:|---|
| 1 | Initial Audit | {{revision}} | {{count}} | {{count}} | {{Fix / Validate / Stabilization}} |

## Validation

| Gate | Target Revision | Evidence | Result |
|---|---|---|---|
| {{repository-controlled gate}} | {{exact full SHA}} | {{durable workflow evidence}} | Pass / Fail / Pending |

## Gate Summary

- Capability Gate 0: Not Required / Pass / Blocked / Incomplete
- Open P0/P1: {{count}}
- Required Validation: Pass / Fail / Pending
- Final Audit: Pass / Fail / Pending
- Candidate readiness: Ready / Not Ready

## Exact-Head Final Audit Boundary

The in-repo ledger cannot embed the SHA of the commit containing that exact
ledger content. Final Audit therefore records the exact pull-request head in
durable external workflow evidence after the final candidate is pushed.

Do not mutate the candidate after Final Audit. Any later push invalidates the
Final Audit and every affected validation or verified finding; review the new
exact head before acceptance.

