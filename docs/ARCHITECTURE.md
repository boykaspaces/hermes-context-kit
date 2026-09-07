# Architecture

## Product layers

```text
versioned specification
  -> portable artifact and state contracts
reference implementation
  -> Skills, profiles, schemas, templates, CLI, and fixtures
consumer adoption
  -> pinned release, selected profile, extensions, and native validation
```

The specification changes only through explicit versioning. The reference
implementation may improve while preserving the current contract. Consumer
repositories never become implicit normative inputs; reusable structural cases
return as anonymized conformance fixtures.

## Profiles

`minimal` supplies identity and current state. `repository` adds Tasks,
decisions, and current-first navigation. `multi-repo` adds System Tasks and an
immutable component graph. Optional features are explicit in
`.hermes/context-kit.json` so filesystem leftovers do not silently enable
behavior.

## Ownership layers

```text
deployment SOUL.md
  -> stable workspace identity and global behavioral boundary
Skill SKILL.md
  -> trigger, guards, and operation routing
Skill reference
  -> detailed protocol for one operation domain
project index
  -> current navigation only
project artifact
  -> state, Task, ADR, Checkpoint, memory, or implementation truth
```

Each concept has one primary owner. Indexes contain routing metadata rather
than copies of the underlying content. Session history is never promoted to
project truth merely because it is recent.

## Retrieval flow

```text
workspace registry
  -> project manifest
  -> project context index
  -> current state or domain index
  -> selected artifact
  -> historical evidence only when required
```

The goal is deterministic reconstruction with the minimum sufficient context,
not preservation of every prior conversation.

## Multi-repository composition

`project-context-management` remains the owner of each repository's local
Task and State lifecycle. `multi-repo-system-management` adds an integration
layer: Component Tasks remain local, while one integration repository owns the
System Task manifest, immutable revision lock, integration evidence, and
deployment truth. A validated Handoff crosses an access boundary without
claiming that the receiving repository changed.

Schema v2 separates source delivery, integration acceptance, verification, and
deployment applicability. A component that is not deployable may still be
locked and verified without a false deployed claim.

## Repository versus runtime

This repository owns reusable specifications, sources, profiles, schemas,
templates, and fixtures. A consuming project owns its adoption manifest,
extensions, current state, and native validation. A consuming deployment owns
its actual `SOUL.md`, workspace identity, registry, runtime Skill copies, and
permissions. Synchronization between repository, project, and runtime is a
separate reviewed action.
