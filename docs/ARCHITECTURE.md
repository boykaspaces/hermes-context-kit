# Architecture

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

## Repository versus runtime

This repository owns reusable sources and templates. A consuming deployment
owns its actual `SOUL.md`, workspace identity, registry, runtime Skill copies,
projects, and permissions. Synchronization between repository and runtime is a
separate operator-controlled action.
