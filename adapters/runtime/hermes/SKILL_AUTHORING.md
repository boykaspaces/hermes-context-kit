# Hermes Skill Authoring Binding

The public Hermes runtime contract fixes the canonical Skill root at
`/home/hermes/.hermes/skills` and the agent-facing management mechanism at
`skill_manage`. Do not infer a different root from a container home, project
directory, or optional `SOUL.md` content.

Hermes deployments may impose concise-description limits and may use a
`metadata.hermes` namespace for runtime-specific discovery. Those fields are
adapter extensions. Portable Skill behavior remains in `SKILL.md` and common
references.

After installation, verify the Skill through Hermes's host-side Skill
management operation and the adapter runtime plan. A file visible only inside
a sandbox is not proof of runtime persistence. SOUL reinforcement is optional
and does not change Skill authoring or installation correctness.
