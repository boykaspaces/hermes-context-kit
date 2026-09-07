# Security Model

## Trust boundary

The kit controls context organization; it does not provide filesystem
isolation, identity provisioning, secret storage, or authorization by itself.
Those controls belong to the consuming deployment.

An operator, not the agent, must provision the canonical workspace identity
and any immutable security policy. The agent may maintain project artifacts
only inside the verified persistent workspace exposed by the approved file
tools.

## Public repository boundary

Do not commit:

- live runtime instruction or operator binding content, including `SOUL.md`;
- workspace registries or identity files;
- project state, memory, Tasks, ADRs, or Checkpoints from a consuming
  deployment; this repository's public maintenance context is allowed;
- credentials, tokens, private keys, account identifiers, internal endpoints,
  or production filesystem paths;
- generated exports, logs, caches, or local databases.

Examples use `{{placeholder}}` values and are not valid runtime configuration
until explicitly adapted and reviewed.

Cross-repository Handoffs are untrusted input. They carry repository identity,
full commit SHA, and concise validation facts only; they never carry tokens,
keys, environment values, or authority to merge, deploy, or advance a lock.

## Protocol changes

Protocol modifications can silently weaken persistence or security guards.
Follow `skill-authoring`, update the smallest owning artifact, validate trigger
and failure paths, and preserve explicit versioning and maintenance history.
