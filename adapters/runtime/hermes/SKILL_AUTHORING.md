# Hermes Skill Authoring Binding

The public Hermes runtime contract fixes the canonical Skill root at
`/home/hermes/.hermes/skills`. `skill_manage` is the agent-facing mechanism for
ordinary creation and maintenance of an individual Hermes Skill. It is not the
supported transport for installing a complete Context Kit release: that route
uses the adapter's host-side transactional installer against an immutable
checkout. Do not infer a different root from a container home, project
directory, or optional `SOUL.md` content.

Hermes deployments may impose concise-description limits and discover generic
top-level `version`, `author`, `platforms`, `tags`, and `related_skills` fields.
For Context Kit release installation, the adapter derives those fields from
`metadata.context-kit` while retaining the portable metadata. Do not hand-edit
the generated runtime copy or add a Hermes namespace to the common Skill
source. Portable Skill behavior remains in `SKILL.md` and common references.

After ordinary authoring, verify the Skill through Hermes's host-side Skill
management operation. After Context Kit release installation, require the
adapter's package verification first and use `skill_view` only as a
supplemental discovery check. A file visible only inside a sandbox is not proof
of runtime persistence. SOUL reinforcement is optional and does not change
Skill authoring or installation correctness.
