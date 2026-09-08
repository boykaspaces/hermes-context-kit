# Project State

Project: hermes-context-kit
Status: Active
Active Task: None

## Current summary

Context Kit 0.5.0 keeps project specification v2 and defines Hermes adapter v3
as a transactional runtime-package contract. Runtime and source-validation
inventories are separate, current complete installation is operator-only, and
SOUL remains optional and user-controlled. AI delivery governance has passed a
minimum documentation-only feasibility check and now has a sequential,
merge-gated experimental rollout covering source design, toolset installation,
existing-project adoption, multi-repository acceptance, and live runtime
verification. This repository now enables the advisory manual contract as an
experimental extension; no core protocol or automation is enabled.

## Primary focus

Keep 0.5.0 consumer acceptance and runtime deployment independent. After the
advisory-contract proposal is accepted, run the first manual dogfood cycle only
through a new Task and pull request.

## Active constraints

- Protocol rules have one canonical owning file.
- Public artifacts contain no consuming deployment state or credentials.
- Breaking protocol changes require an explicit specification version and
  migration path.
- Existing consumer assumptions are evidence for fixtures, not universal
  public requirements.
