# Hermes Runtime Adapter

Use this adapter when a Hermes deployment manages Context Kit projects.

The operator integrates
[`templates/SOUL.project-context.example.md`](./templates/SOUL.project-context.example.md)
into the deployment-owned `SOUL.md`. That file owns the workspace root,
identity marker, registry, approved Skill installation mechanism, and runtime
Skill root. None of those values belongs to the portable core or a consuming
project repository.

The common Skills use portable `name` and `description` frontmatter. Hermes may
ignore the `metadata.context-kit` namespace while retaining it for related-Skill
routing and release validation.

Use [`SKILL_AUTHORING.md`](./SKILL_AUTHORING.md) when rendering or installing a
reusable Skill for Hermes.
