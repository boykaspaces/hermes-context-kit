# ADR-002: Separate the Neutral Core from Runtime and Workflow Adapters

Status: Active
Decision Area: Public Protocol Architecture
Supersedes: ADR-001

## Context

The 0.2 protocol describes itself as portable but its normative Skill and
profile contracts still name Hermes runtime concepts such as `SOUL.md`, the
`.hermes/` directory, `AGENTS.md`, and `metadata.hermes`. The first full
multi-repository rollout also required a follow-up pull request because the
protocol did not distinguish candidate state in a change proposal from the
canonical state on its accepted branch.

## Decision

Context Kit will separate four ownership layers:

1. a runtime-neutral project-management and reusable-capability core;
2. runtime adapters that bind the core to agent-specific instruction files,
   workspace configuration, Skill packaging, and installation mechanisms;
3. workflow adapters that map neutral proposal and acceptance semantics to a
   forge or delivery system; and
4. consumer-owned extensions and deployment bindings.

Project specification v2 uses the neutral `.context-kit/` namespace and
logical profile artifacts. Hermes and Codex are reference runtime adapters;
GitHub is the first workflow adapter. Version 1 `.hermes/` projects remain
explicit compatibility input and migrate through a dry-run-first flow.

The accepted integration branch owns canonical repository state. A proposal
branch contains a candidate next state; merging the proposal activates that
state atomically. The final System proposal is updated after Component
proposals merge and includes the accepted revisions, verification, and
completed Task state. Its own merge is not recursively recorded inside itself.

## Rationale

This preserves explicit state without making one agent runtime or one forge a
universal requirement. Treating merge as activation makes the accepted branch
truthful while eliminating routine post-merge reconciliation proposals.

## Alternatives Considered

- Keep Hermes terminology but call it generic: rejected because consumers
  would still need to emulate Hermes configuration and paths.
- Move only the `SOUL.md` example: rejected because normative Skills, profiles,
  validation, and authoring rules would remain coupled.
- Require a follow-up proposal after every merge: rejected because it creates
  recursive administrative work without improving the accepted state.
- Let a bot write completion state directly after merge: retained as an
  optional workflow-adapter optimization, not a core requirement, because it
  requires elevated repository authority.

## Consequences

- The v2 artifact namespace and adoption schema are breaking changes.
- Runtime-specific templates and authoring rules move under adapters.
- The reference CLI must support neutral initialization and reviewed v1-to-v2
  migration.
- Consumer migrations remain separate acceptance events after the new release
  passes neutral, Hermes, Codex, and GitHub workflow fixtures.
