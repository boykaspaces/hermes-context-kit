# Hermes Skill Authoring Binding

The Hermes deployment contract owns the canonical Skill root and approved
installation mechanism. Resolve both from the operator-owned `SOUL.md`; never
infer them from a home directory or container path.

Hermes deployments may impose concise-description limits and may use a
`metadata.hermes` namespace for runtime-specific discovery. Those fields are
adapter extensions. Portable Skill behavior remains in `SKILL.md` and common
references.

After installation, verify the Skill through Hermes's host-side Skill
management operation. A file visible only inside a sandbox is not proof of
runtime persistence.
