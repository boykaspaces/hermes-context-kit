# ADR-001: Publish a Versioned, Profile-Based Public Protocol

Status: Superseded
Decision Area: Public Protocol Architecture
Superseded-By: ADR-002

## Context

Hermes Context Kit is intended to let an unfamiliar agent bootstrap and manage
a new project without access to any existing consumer repository or private
deployment. The current repository mixes stable protocol intent, reference
implementation details, and assumptions learned from its first consumers.
That makes strict validation vulnerable to consumer-specific coupling and
makes compatible upgrades difficult to distinguish from protocol changes.

## Decision

Publish Context Kit as three related but separate layers:

1. a small, versioned public specification for project identity, current state,
   Tasks, decisions, evidence, and optional cross-repository coordination;
2. a reference implementation containing Skills, neutral templates, schemas,
   deterministic bootstrap/migration/validation tools, and conformance
   fixtures; and
3. an adoption contract recorded by each consuming project, including the
   specification version, Kit version, selected profile, and enabled features.

The default profile is a minimal single-project core. Repository context and
multi-repository coordination are opt-in profiles. Core schemas validate stable
required fields while providing explicit extension points for consumer-owned
metadata. Protocol-breaking changes require a new specification version and a
documented, dry-run migration path. Published versions are immutable; consumers
pin accepted versions rather than depending on a mutable branch.

Public validation remains offline and consumer-neutral. Context Kit owns
portable conformance fixtures; each consuming repository owns validation of its
project-specific extensions and adoption state.

## Rationale

This model gives new users one deterministic path from an empty repository to a
recoverable project while keeping simple projects small. It prevents private
deployment history from becoming a universal rule, permits independent
consumer evolution, and makes upgrades reviewable and reversible.

## Alternatives Considered

- Preserve the current template-only model: rejected because adoption and
  upgrades would continue to depend on agent interpretation.
- Encode the private operations repository as the canonical schema: rejected
  because it is not portable and Hermes cannot inspect it independently.
- Require every project to adopt every Context Kit feature: rejected because
  System Tasks, component locks, deployment evidence, and memory are not
  necessary for ordinary single-repository projects.
- Track Context Kit from mutable main: rejected because protocol behavior
  could change without an explicit consumer acceptance event.

## Consequences

- Context Kit needs explicit specifications, schemas, profiles, lifecycle
  tooling, and previous-version fixtures.
- Existing repositories will migrate through separate Component Tasks after
  the new contract passes Context Kit conformance tests.
- Temporary compatibility readers may be required, but legacy representation
  does not permanently define the public core.
- Consumer-specific deployment bindings remain owned and validated by the
  consumer rather than by the portable core.
