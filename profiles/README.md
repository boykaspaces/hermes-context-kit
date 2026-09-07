# Adoption Profiles

Profiles select coherent project-context capabilities without changing the core
ownership model.

| Profile | Use when |
|---|---|
| [minimal](./minimal/profile.json) | A new or small project needs identity and resumable state only |
| [repository](./repository/profile.json) | A repository needs persistent Tasks and durable decisions |
| [multi-repo](./multi-repo/profile.json) | An integration owner coordinates immutable component revisions |

Profile definitions are consumed by `scripts/context_kit.py`. They require
logical artifacts whose repository-relative paths are owned by the current
specification, so runtime filenames do not leak into the core profile.
Features are explicit so an agent does not infer capabilities from stray files.

`repository` and `multi-repo` allow the optional `checkpoints` and `memory`
features. The initializer creates their indexes only when explicitly selected.
