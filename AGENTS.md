# Repository AI Instructions

## Entry and retrieval

- Start with `README.md`; use `.hermes/context-index.md` for repository
  maintenance state.
- Read `.hermes/context-kit.json` before changing adopted project context.
- Follow the narrowest `Read when` route.
- Read a Skill's complete `SKILL.md` before changing that Skill.
- Load only the reference files required by the operation being changed.

## Project and system context

- Use `project-context-management` for this repository's Task, State,
  Checkpoint, ADR, and index mutations.
- Also use `multi-repo-system-management` when work has a parent System Task,
  changes another repository, advances a component revision, or requires an
  integration Handoff.
- If the integration repository is inaccessible, produce a validated Handoff;
  do not claim its Task, lock, or deployment state changed.

## Editing boundaries

- `spec/` owns versioned public contracts; `profiles/` owns adoption feature
  sets; Skills own agent operating behavior.
- Preserve one owning file for each protocol rule.
- Update affected indexes when paths, names, status, or routing change.
- Keep templates neutral and use `{{placeholder}}` for deployment values.
- Never add live project state, credentials, account identifiers, or private
  operating records from a consuming deployment. Public repository-maintenance
  context is allowed only when it contains no deployment-specific data.
- Treat files under `skills/` as protocol source, not documentation examples.

## Validation

- Run `scripts/validate.sh` after any change.
- Verify Markdown links, Skill metadata, reference routing, placeholders, and
  the absence of forbidden private identifiers.
