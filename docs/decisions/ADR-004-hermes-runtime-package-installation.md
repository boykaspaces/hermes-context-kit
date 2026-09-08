# ADR-004: Treat Hermes Skill Sets as Transactional Runtime Packages

Status: Active
Decision Area: Hermes Runtime Package Installation
Supersedes: —
Superseded-By: —

## Context

Hermes adapter v2 treated every file under a source Skill directory as a
runtime-installation file and described `skill_manage` as a complete install
mechanism. Current Hermes accepts supporting writes only below `references/`,
`templates/`, `scripts/`, and `assets/`; source `tests/` therefore cannot be
installed that way. The tool also requires file bodies to pass through the
model and has no operation that imports an exact tree from an immutable
checkout.

Individual Hermes batches are atomic but capped at 20 operations. Each Context
Kit Skill can fit one batch after source-only tests are excluded, but a complete
multi-Skill release still spans batches and may expose a mixed revision set.
The v2 operator installer also activated Skills sequentially before writing its
manifest, so process interruption could leave the same ambiguity.

Hermes discovery reads its standard fields or generic top-level fallbacks; it
does not derive tags or related-Skill routing from `metadata.context-kit`.

## Decision

1. The adapter publishes disjoint `runtime_inventory` and
   `source_validation_inventory` values. Only `SKILL.md` and files below the
   four Hermes-supported directories belong to the runtime inventory.
2. The adapter deterministically renders Hermes-compatible runtime frontmatter
   while retaining the portable source metadata. Installed hashes describe the
   rendered runtime artifact, not an assumed byte-for-byte source copy.
3. Complete release installation is operator-only until Hermes exposes a
   trusted immutable-tree import operation. `skill_manage` remains valid for
   normal Skill authoring but is not advertised as the release installer.
4. One install manifest owns package state. `staging` and `failed` are not
   ready; only a manifest whose revision, capabilities, workspace, and complete
   runtime inventories verify may become `ready`.
5. The operator installer stages every Skill before activation, journals prior
   targets, rolls all touched Skills back after an ordinary failure, and
   exposes an explicit rollback route for an interrupted transaction.
6. An installation-only Context Kit checkout is source material, not a managed
   project. The Hermes adapter gives it a non-project source-cache path.
   A checkout intentionally placed under `/workspace/projects/<project_id>` is
   a managed project and requires normal Workspace Registry enrollment.

## Rationale

The immutable Context Kit revision is the compatibility unit; individual Skill
version numbers need not match. Separating source validation from runtime
payloads matches Hermes's actual loading boundary, while a journaled package
state makes partial activation visible and recoverable. Keeping runtime
metadata rendering inside the adapter preserves a single portable Skill source.

## Alternatives Considered

- Inline every source file through `skill_manage`: rejected because source-only
  paths are forbidden and large payloads pass through model context.
- Treat each successful Skill batch as a complete upgrade: rejected because a
  multi-Skill capability set can still be mixed.
- Add `metadata.hermes` to portable Skill sources: rejected because it couples
  common artifacts to one runtime.
- Assume a future `import_tree` operation: rejected until the deployed Hermes
  contract actually provides and validates it.

## Consequences

- Adapter v3 is a breaking runtime-contract update but does not change project
  specification v2 or consumer project artifacts.
- Agents without an approved host operator route must report installation as
  Pending user and provide exact resume evidence.
- Existing v2 install manifests require a reviewed v3 reinstall before they
  can satisfy readiness.
- A source checkout under the canonical project root remains usable, but its
  project navigation is Incomplete until registry enrollment succeeds.
