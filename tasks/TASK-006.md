# TASK-006: Make Hermes Adoption Skill-First

Status: Completed
Priority: High

## Goal

Make the public Hermes adapter self-describing and executable for a first-time
agent: install and verify the required Context Kit Skills at the solution's
fixed runtime paths, then offer—but never require or silently apply—the
optional SOUL reinforcement.

## Completed

- Reviewed the latest `main` from a clean first-access perspective.
- Confirmed the current Hermes deployment paths and the absence of an
  agent-facing host-side SOUL management tool.
- Approved Skill-first adoption with SOUL as an optional user choice.
- Added a public machine-readable Hermes runtime contract, consumer config
  schema, fixed capability mapping, and deterministic setup utility.
- Added exact-revision and clean-checkout guards, complete Skill inventories,
  explicit replacement and rollback behavior, workspace provisioning, and
  runtime verification.
- Made Skill verification the runtime-readiness boundary and made the SOUL
  preview/application a separate, explicit user choice that preserves existing
  content.
- Removed private-operations and optional-standing-instruction dependencies
  from the portable Skill rules.
- Added first-access documentation, upgrade guidance, conformance coverage,
  and cold-start tests.
- Passed the complete repository validation suite.

## Remaining

None.

## Blockers

None.

## Relevant Files

- `adapters/runtime/hermes/`
- `docs/ADOPTION.md`
- `scripts/context_kit.py`
- `tests/`
- `docs/decisions/ADR-003-skill-first-hermes-adoption.md`

## Related Decisions

- ADR-002
- ADR-003

## Result

Hermes can now install and verify Context Kit from this public repository
without private Ops documentation or SOUL mutation. Once verification reports
the runtime ready, the setup output directs the agent to show the optional SOUL
reinforcement and apply it only if the user chooses.

## Next Step

None.
