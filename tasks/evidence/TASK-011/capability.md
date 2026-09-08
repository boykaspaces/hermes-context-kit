# Capability Audit — TASK-011

Status: Passed
Gate Result: Pass

## Required Guarantees

| ID | Guarantee | Required Primitive | Evidence | Failure Boundary | Result | Disposition |
|---|---|---|---|---|---|---|
| CAP-1 | Review can identify an immutable Git candidate | Git commit object identity | Git object model and the configured GitHub workflow adapter | Mutable branch name | Supported | Keep |
| CAP-2 | An in-repo ledger can embed the SHA of the commit containing that exact ledger content | A non-self-referential containing-commit identity | Content-addressed commit construction: changing the embedded SHA changes the tree and commit | Ledger update after candidate creation | Unsupported | Reduce Contract |
| CAP-3 | Final Audit can bind to the exact pull-request head without another candidate commit | Workflow-visible head SHA plus durable external review evidence | GitHub workflow adapter candidate model and pull-request review boundary | New push after audit | Supported | Keep |

## Disposition

CAP-2 reduces the contract:

- The in-repo ledger records the frozen contract and review history but does
  not claim to embed the SHA of the final commit that contains itself.
- Final Audit evidence is external workflow evidence that identifies the exact
  full pull-request head SHA.
- No candidate mutation is allowed after Final Audit. A new push invalidates
  the audit and requires a new exact-head review.

This is evidence placement, not a weaker review target: the Final Auditor still
reviews the exact candidate proposed for acceptance.

## Gate Result

PASS — the unsupported self-reference guarantee was removed before template
implementation, and no retained required guarantee remains Unknown.
