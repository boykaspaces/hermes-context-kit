# Project State

Project: hermes-context-kit
Status: Active
Active Task: None

## Current summary

Context Kit 0.3.0 defines a v2 runtime-neutral core under `.context-kit/`,
versioned Hermes and Codex runtime adapters, a GitHub workflow adapter, and a
guarded v1-to-v2 migration path. A proposal carries its complete candidate
state and its acceptance activates that state without a routine follow-up
proposal.

## Primary focus

No active Task. Consumer adoption should start as an explicit multi-repository
System Task that selects adapters and preserves each consumer's extensions.

## Active constraints

- Protocol rules have one canonical owning file.
- Public artifacts contain no consuming deployment state or credentials.
- Breaking protocol changes require an explicit specification version and
  migration path.
- Existing consumer assumptions are evidence for fixtures, not universal
  public requirements.
