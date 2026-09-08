# Project State

Project: hermes-context-kit
Status: Active
Active Task: None

## Current summary

Context Kit 0.4.0 defines a v2 runtime-neutral core under `.context-kit/`,
versioned Hermes and Codex runtime adapters, a GitHub workflow adapter, and a
guarded v1-to-v2 migration path. Hermes adoption is now self-describing and
Skill-first; SOUL reinforcement is optional and user-controlled.

## Primary focus

Publish the 0.4.0 candidate and then adopt its accepted revision in consumers
through their own reviewed integration Tasks.

## Active constraints

- Protocol rules have one canonical owning file.
- Public artifacts contain no consuming deployment state or credentials.
- Breaking protocol changes require an explicit specification version and
  migration path.
- Existing consumer assumptions are evidence for fixtures, not universal
  public requirements.
