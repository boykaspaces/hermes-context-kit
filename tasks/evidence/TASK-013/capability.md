# Capability Audit — TASK-013

Status: Passed
Applicability: Required
Gate Result: Pass

## Environment

- Accepted repository base: `4c31db3605739d3afd4769f17c20135a2b66ef18`
- Runtime adapter: Hermes v3 operator package route
- Evidence date: 2026-09-09
- Prototype source: isolated local clone with no mutation to the accepted repository
- Prototype revision: `10e8beb8f6685a4b9aeb93920755eb79307e4d7f`
- Prototype runtime: isolated temporary filesystem paths

## Required Guarantees

| ID | Guarantee | Required Primitive | Evidence | Failure Boundary | Result | Disposition |
|---|---|---|---|---|---|---|
| CAP-1 | A new optional capability can select a standalone Skill without changing installer architecture | Contract-driven capability-to-Skill mapping | Isolated prototype selected `project-context-management` and `ai-delivery-governance` | Hard-coded known-Skill list outside the contract | Supported | Keep |
| CAP-2 | The installed governance inventory can include its entry point, reference, and templates | Existing runtime inventory classifier | Prototype inventory contained `SKILL.md`, `references/delivery-cycle.md`, and `templates/capability-audit.md` | External files omitted from the package or copied from non-runtime paths | Supported | Keep |
| CAP-3 | The selected package can reach verified ready state in isolation | Existing transactional install and verify operations | Fresh prototype install returned `ready: true` and `install_state: ready` | Partial copy or manifest-only readiness | Supported | Keep |
| CAP-4 | Upgrade, ordinary-failure rollback, and interrupted recovery can apply to the new optional Skill | Existing package transaction journal and inventory comparison | Accepted Hermes installer tests cover capability expansion, multi-Skill rollback, fail-closed staging, and explicit recovery | Capability-specific behavior diverges from generic transaction handling | Supported | Keep and add focused regression evidence |
| CAP-5 | Source packaging proves installation in a live Hermes runtime | Host-owned runtime mutation and discovery evidence | The experiment used isolated paths only | Sandbox or source acceptance misreported as live installation | Unsupported | Reduce Contract |

## Prototype Evidence

The second isolated probe selected these Skills:

```text
project-context-management
ai-delivery-governance
```

Its governance runtime inventory was:

```text
SKILL.md
references/delivery-cycle.md
templates/capability-audit.md
```

The installer classified both Skills as fresh, created the isolated workspace
identity and registry, committed the package, and returned:

```json
{
  "install_state": "ready",
  "ready": true
}
```

## Contract Reduction

- TASK-013 proves source packaging and isolated operator-route behavior only.
- Live runtime installation remains Increment 8 and requires host-side
  installation and discovery evidence.
- Existing-project adoption remains Increment 6 and cannot be inferred from
  this package test.
- No new installer architecture or agent-side release installation route is
  included.

## Gate Result

PASS — every guarantee retained by the frozen contract has a supported
primitive. The unsupported live-installation inference was removed from this
Task rather than accepted as risk.
