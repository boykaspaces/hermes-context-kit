# Capability Audit — TASK-{{task_id}}

Status: Draft
Applicability: Required
Gate Result: Incomplete

## Minimum Desired Outcome

{{smallest outcome the Task must preserve}}

## Required Guarantees

| ID | Guarantee | Required Primitive | Evidence | Failure Boundary | Result | Disposition |
|---|---|---|---|---|---|---|
| CAP-1 | {{observable guarantee}} | {{actual primitive}} | {{stable evidence pointer}} | {{critical failure boundary}} | Supported / Unsupported / Unknown | Keep / Reduce Contract / Accept Risk / Add Dependency |

## Dispositions

For every non-`Keep` row, record:

- Capability ID: {{CAP-N}}
- Contract effect: {{removed, weakened, risk accepted, or dependency added}}
- Authority: {{required for Accept Risk; otherwise Not Applicable}}
- Approval evidence: {{required for Accept Risk; otherwise Not Applicable}}
- Known failure mode: {{concrete failure}}
- Recovery action: {{operator or system recovery}}
- Reevaluation condition: {{fact that requires another audit}}

## Evidence Boundaries

- Environment or profile: {{exact identity or explicit limitation}}
- Positive evidence: {{specification, source, or executable result}}
- Negative or failure evidence: {{adversarial result or reason not required}}
- Not proved: {{claims this audit does not make}}

## Gate Evaluation

- Required guarantees retained by the contract: {{IDs}}
- Retained Unknown guarantees: {{None or IDs}}
- Unresolved dependencies: {{None or IDs}}
- Authorized risk acceptances: {{None or IDs plus evidence}}

Gate Result: `Not Required | Pass | Blocked | Incomplete`

`Pass` is valid only when every guarantee retained by the frozen contract is
Supported or covered by explicit authorized risk acceptance. An unresolved
dependency is `Blocked`; a required Unknown is `Incomplete`.
