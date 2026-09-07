# Codex Skill Authoring Binding

Install Skills through Codex's supported Skill mechanism. A Codex Skill
requires a directory containing `SKILL.md` with `name` and `description`
frontmatter; supporting `scripts/`, `references/`, and `assets/` are optional.

`agents/openai.yaml` may provide UI metadata and invocation policy when the
target installation supports it. Preserve existing policy and dependency
fields when changing only UI metadata.

Resolve the configured Codex Skill root from the runtime rather than assuming a
user-home path. Validate installation and discovery after creation.
