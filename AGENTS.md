# Repository AI Instructions

## Entry and retrieval

- Start with `README.md`.
- Follow the narrowest `Read when` route.
- Read a Skill's complete `SKILL.md` before changing that Skill.
- Load only the reference files required by the operation being changed.

## Editing boundaries

- Preserve one owning file for each protocol rule.
- Update affected indexes when paths, names, status, or routing change.
- Keep templates neutral and use `{{placeholder}}` for deployment values.
- Never add live project state, credentials, account identifiers, or private
  operating records.
- Treat files under `skills/` as protocol source, not documentation examples.

## Validation

- Run `scripts/validate.sh` after any change.
- Verify Markdown links, Skill metadata, reference routing, placeholders, and
  the absence of forbidden private identifiers.
