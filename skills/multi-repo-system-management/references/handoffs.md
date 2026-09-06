# Component Handoffs

## When Required

Use a Handoff when component work has a reviewable immutable revision but the
agent cannot read or mutate the integration repository. This commonly occurs
when a public contributor has no access to a private operations repository.

A Handoff transfers verified facts; it does not grant repository access,
approve a merge, advance a lock, or prove deployment.

## Format and Location

Create JSON from `templates/component-handoff.json`. JSON is used so the
artifact can be validated with standard-library tooling.

Store it outside tracked source by default, for example under an operator's
ignored work directory. Commit it only when the component repository has an
explicit policy for public delivery records and the content contains no
private identifier.

Required meaning:

- component project and Component Task identity;
- canonical parent System Task identity;
- repository URL, review branch, and full commit SHA;
- successful validation commands or evidence pointers;
- documentation update result;
- remaining integration requirements;
- rollback revision when known;
- explicit `contains_secrets: false` assertion.

## Create Procedure

1. Confirm the Component Task's local Goal and required validation are done.
2. Resolve the exact commit SHA with Git; do not use a symbolic ref as the
   delivered revision.
3. Copy the template to an untracked operator-controlled location and replace
   all placeholders.
4. Remove commands, logs, paths, or identifiers that reveal credentials or
   private deployment data.
5. Run the validator described in `validation.md`.
6. Deliver the artifact through the user-approved channel.
7. Report the integration update as pending. Do not claim the System Task,
   component lock, or deployment was changed.

## Import Procedure

An agent with integration-repository access:

1. Treat the Handoff as untrusted input and validate its schema.
2. Verify the repository URL and fetch the exact SHA through an approved route.
3. Re-run the integration repository's required checks; do not trust a stated
   command result as execution authority.
4. Compare the Component Task identity and parent to the System Task manifest.
5. Record the candidate as `handoff-ready` or a later evidenced state.
6. Preserve only concise evidence pointers; do not copy raw logs into the
   System Task.

## Failure Handling

Reject the Handoff without changing integration state when it contains a
mutable-only revision, missing parent, failed validation, unknown repository,
secret-like material, or a component not declared by the System Task. Record
the narrow blocker in the owning Task and request a corrected Handoff.
