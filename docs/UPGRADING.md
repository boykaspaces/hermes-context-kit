# Upgrade and Migration

## Contract

Consumers pin an immutable Context Kit release in
`.context-kit/manifest.json`. They never treat mutable `main` as an accepted
protocol version.

Version 1 consumers use `.hermes/context-kit.json`. The v2 migration command
reads it only as legacy input and does not silently delete it.

A compatible implementation update may preserve the current specification
version. A change that rejects a previously conforming artifact, changes
canonical ownership, or changes state meaning requires a new specification
version.

## Procedure

1. Check out the target immutable release separately from the installed/current
   version.
2. Run both release validators on their own source trees.
3. Run `context_kit.py migrate --to-spec 2 --check` from the target release
   against the consumer and select runtime adapters explicitly.
4. Review the planned files, semantic state changes, unsupported extensions,
   and required owner actions.
5. Preserve the current Git diff or a complete recoverable backup.
6. Apply the migration only with explicit target-version authorization.
7. Run Context Kit validation and the consumer's native validation.
8. Remove legacy duplicate paths in the reviewed migration proposal only after
   v2 validation passes.
9. Update the pinned release only after acceptance.
10. Retain the previous release until the upgraded project has been recovered
   successfully in a fresh agent session.

## Failure handling

Migration stops rather than guessing when:

- project identity is ambiguous;
- a legacy lock mixes core revisions with consumer deployment bindings;
- an extension has no target owner;
- a current Task pointer is inconsistent;
- required evidence is prose rather than a stable pointer;
- a repository needed for relationship validation is inaccessible.

Repair through the owning project, rerun the audit, and do not update the pin
merely to silence validation.
