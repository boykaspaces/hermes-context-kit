# Project State

Project: hermes-context-kit
Status: Active
Active Task: None

## Current summary

Context Kit 0.5.0 keeps project specification v2 and defines Hermes adapter v3
as a transactional runtime-package contract. Runtime and source-validation
inventories are separate, current complete installation is operator-only, and
SOUL remains optional and user-controlled.

## Primary focus

Publish the 0.5.0 candidate, then let each consumer independently accept the
reviewed revision. Runtime deployment remains a separate operator boundary.

## Active constraints

- Protocol rules have one canonical owning file.
- Public artifacts contain no consuming deployment state or credentials.
- Breaking protocol changes require an explicit specification version and
  migration path.
- Existing consumer assumptions are evidence for fixtures, not universal
  public requirements.
