# TASK-013: Package Advisory Governance as an Installable Toolset

Status: Completed
Governance: Required
Priority: High
Depends-On:
  - TASK-011
  - TASK-012

## Goal

Package the proven advisory delivery-governance procedure, evidence templates,
and runtime metadata as one versioned optional Skill that the existing Hermes
transactional installer can select, install, verify, upgrade, and recover in
isolated paths.

## Acceptance Criteria

- AC-1: `ai-delivery-governance` is a standalone experimental Skill with
  precise triggers, a single canonical procedure reference, packaged evidence
  templates, and explicit portable version metadata.
- AC-2: Existing experimental documentation becomes a compatibility route to
  the Skill-owned canonical procedure and templates; normative rules are not
  duplicated between owners.
- AC-3: The Hermes runtime contract, configuration schema, public setup route,
  and source inventory expose `delivery-governance` as optional while
  `project-context` remains required.
- AC-4: A clean isolated installation selects the complete governance runtime
  inventory and verifies `ready: true` for the exact source revision.
- AC-5: An isolated upgrade from the previously accepted Kit package adds the
  optional governance Skill without treating source acceptance as live-runtime
  installation.
- AC-6: Injected ordinary failure restores the previous package and manifest;
  interrupted installation fails closed until the documented rollback route
  recovers it.
- AC-7: Repository validation and exact-head workflow checks pass without
  changing the frozen `project-context-management` protocol, Task statuses,
  project schema, governance automation, consumer repositories, component
  locks, deployment bindings, or a live Hermes runtime.

## Supported Scope

- One medium-complexity portable Skill containing one procedure reference and
  two evidence templates.
- The existing Hermes v3 operator-owned transactional package installer.
- Isolated filesystem fixtures representing clean install, package upgrade,
  ordinary-failure rollback, and interrupted-install recovery.
- Source and runtime inventory routing required to discover and select the
  optional capability.

## Out of Scope

- Installing into `/home/hermes/.hermes` or any other live Hermes runtime.
- Adopting the capability in an existing consumer project; Increment 6 owns
  that validation after this proposal is accepted.
- Advancing a component lock, integration state, or deployment binding.
- Adding a governance JSON schema, CLI, CI gate, automatic reviewer, merge,
  installation, deployment, or continuous execution.
- Modifying any file under `skills/project-context-management/`.

## Capability Audit

Applicability: Required
Gate Result: Pass
Matrix: `tasks/evidence/TASK-013/capability.md`

The isolated prototype proved that the current data-driven Hermes installer
can select a new optional capability, include its Skill entry point,
reference, and template in the runtime inventory, install the package, and
verify it ready. The formal implementation therefore does not require a new
installation architecture.

## Required Validation

- `python3 -m unittest tests.test_hermes_runtime_setup`
- `./scripts/validate.sh`
- Isolated clean installation with complete governance inventory verification.
- Isolated accepted-base-to-candidate package upgrade.
- Injected ordinary-failure rollback and interrupted-install recovery.
- Exact-head GitHub workflow checks and Final Audit evidence.

## Review

Ledger: `tasks/evidence/TASK-013/review.md`

## Completed

- Confirmed PR #11 is accepted on `main`.
- Qualified the recurring, non-obvious, twice-dogfooded procedure as a
  standalone optional Skill candidate.
- Passed a no-source-mutation feasibility probe against accepted commit
  `4c31db3605739d3afd4769f17c20135a2b66ef18`.
- Verified that `SKILL.md`, one reference, and one template enter the selected
  runtime inventory and produce `ready: true` in an isolated install.
- Reduced the formal design to the existing installer and inventory model.
- Implemented the standalone Skill, canonical compatibility routes, optional
  Hermes capability mapping, and capability-specific transaction tests in
  candidate `bb223e8171a0d0a6d9d2c7d0e3ca482e38d9d3ba`.
- Completed Initial Audit with one P1 installation-versus-load boundary
  finding and one P2 command-parser coverage finding.
- Resolved R-001 by separating runtime preparation from project/Task load
  eligibility in the public installation route.
- Resolved R-002 with a direct `configure --capability delivery-governance`
  parser regression test.
- Delta Review verified both fixes and the 21 focused Hermes runtime tests.
- Passed an isolated upgrade from accepted base
  `4c31db3605739d3afd4769f17c20135a2b66ef18` to candidate
  `f276f5ed6f685fd057a74c74d40da120404e39ee`; the existing Skill remained
  identical, the governance Skill installed fresh, and verification returned
  ready with all four runtime files.
- Verified ordinary-failure rollback restores the previous ready package and
  interrupted governance installation fails closed until explicit rollback.
- Passed the complete repository validation after Delta Review.
- Prepared the exact-head Final Audit boundary for GitHub workflow evidence
  and separate user acceptance.

## Remaining

None.

## Blockers

None.

## Result

The advisory governance procedure is now packaged as version `0.1.0` of the
independent optional `ai-delivery-governance` Skill. The existing Hermes v3
installer selects it through the `delivery-governance` capability, records its
complete runtime inventory, expands an accepted base package transactionally,
restores the prior ready package after ordinary failure, and fails closed on
interruption. Installation remains distinct from project adoption and from a
live Hermes deployment.

## Relevant Files

- `skills/ai-delivery-governance/`
- `skills/README.md`
- `adapters/runtime/hermes/runtime-contract.json`
- `adapters/runtime/hermes/runtime-config.schema.json`
- `adapters/runtime/hermes/README.md`
- `tests/test_hermes_runtime_setup.py`
- `docs/experiments/DELIVERY_GOVERNANCE_V1.md`
- `docs/experiments/templates/`
- `tasks/evidence/TASK-013/`

## Next Step

None for TASK-013. After this proposal is accepted, create a new project-owned
Task for the existing-project adoption pilot described as Increment 6.
