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

## Context Kit 0.4 and Hermes adapter v2

Context Kit 0.4 keeps project specification v2 and changes only the Hermes
runtime-adoption contract. Hermes adapter v2 makes Skills sufficient, fixes the
solution's runtime and workspace paths in a public machine-readable contract,
and makes SOUL reinforcement optional.

When upgrading a Hermes consumer from adapter v1:

1. check out the accepted 0.4 commit separately;
2. generate and review a Hermes runtime configuration through
   `adapters/runtime/hermes/scripts/runtime_setup.py configure`;
3. preview, install, and verify the selected Skill inventory;
4. update the consumer manifest to Kit 0.4 and Hermes adapter version 2 in the
   same reviewed proposal;
5. keep any existing SOUL content unchanged unless the user separately chooses
   the optional reinforcement; and
6. retain the prior Skill copies and consumer revision for rollback.

An existing Context Kit block in SOUL may remain. It is no longer acceptance
evidence and its absence is not a migration failure.

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
