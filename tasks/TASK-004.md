# TASK-004: Design the Public Context Kit Protocol

Status: Completed
Type: Component
Priority: High
Parent System Task: personal-hermes-agent:TASK-014

## Goal

Turn Hermes Context Kit into a versioned, consumer-neutral project-management
and Skill-authoring protocol that an unfamiliar agent can use to bootstrap,
validate, maintain, and upgrade a new project from zero.

## Completed

- Audited PR #1 and reproduced its macOS path and current-consumer
  compatibility failures.
- Agreed that Context Kit owns a minimal public contract while consumers own
  project-specific extensions and final acceptance.
- Recorded the versioned, profile-based architecture in ADR-001.
- Defined versioned minimal, repository, and multi-repository profiles with a
  machine-readable adoption manifest and portable schemas.
- Added deterministic init, validate, doctor, and guarded migration commands.
- Separated source, acceptance, and deployment state in System Task schema v2
  while retaining explicit v1 historical compatibility.
- Added cross-platform CI, clean-room fixtures, consumer-extension coverage,
  and transactional migration tests.
- Integrated the useful hardening work from PR #1 and fixed its macOS path,
  Markdown pointer, and rich consumer lock compatibility failures.

## Remaining

None. Consumer adoption and system-level acceptance are owned by parent System
Task `personal-hermes-agent:TASK-014`.

## Blockers

None.

## Relevant Files

- docs/decisions/ADR-001-versioned-profile-based-public-protocol.md
- spec/
- schemas/
- profiles/
- skills/
- templates/
- scripts/
- tests/fixtures/

## Related Decisions

- ADR-001

## Next Step

None.

## Result

Context Kit 0.2.0 is a self-describing, profile-based public protocol with a
portable reference implementation. Repository validation and clean-room
bootstrap, doctor, migration, extension, and System Task v2 tests pass.
