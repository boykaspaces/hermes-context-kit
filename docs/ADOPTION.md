# Adoption Guide

Hermes Context Kit is a public protocol and reference implementation for
starting and maintaining agent-managed projects. A consuming agent needs only
an explicit Context Kit release and access to the target project directory.

## Start a new project

Check out an immutable release or reviewed commit. Do not initialize from a
mutable branch without recording its exact revision.

Preview the write set:

```sh
python3 scripts/context_kit.py init \
  --root <target-project> \
  --project-id <stable-project-id> \
  --name "<project name>" \
  --goal "<project goal>" \
  --profile repository \
  --dry-run
```

Run the same command without `--dry-run` after the target and profile are
confirmed. Initialization never overwrites a different existing file. Validate
the result:

```sh
python3 scripts/context_kit.py validate --root <target-project>
```

The generated `.hermes/context-kit.json` records the specification version,
Kit release, profile, enabled features, and consumer extension namespace.

## Choose a profile

| Profile | Includes | Use when |
|---|---|---|
| `minimal` | Identity, local instructions, adoption metadata, current state | A small or new project does not yet need durable work indexes |
| `repository` | Minimal + Tasks + decisions + context index | A repository needs multi-session maintenance |
| `multi-repo` | Repository + System Task routing + component lock | One integration owner coordinates multiple repositories |

The `repository` and `multi-repo` profiles may enable `checkpoints` or
`memory` with repeatable `--feature` arguments. Do not enable an empty feature
only to populate the tree.

## Adopt an existing project

Audit without mutation:

```sh
python3 scripts/context_kit.py migrate --root <project> --check
```

For minimal or repository projects, `--apply` adds the adoption manifest and
then validates existing state. A legacy multi-repository project requires a
reviewed lock/state migration before application; the tool reports this
explicitly rather than duplicating or discarding its current lock.

See [`UPGRADING.md`](./UPGRADING.md) for version changes and rollback.

## Install Skills

The checkout is the release source; it is not automatically the runtime Skill
directory. Install only the required Skill directories through the consuming
agent runtime's supported Skill mechanism:

```text
skills/project-context-management/
skills/skill-authoring/
skills/multi-repo-system-management/   # multi-repo profile only
```

Preserve each directory without flattening it. Record the exact Context Kit
release, verify the installed file inventory, and keep the previous immutable
version available for rollback. Do not infer a runtime Skill path from a
container home directory or copy Skills into the project root.

## Optional deployment workspace

A long-running Hermes deployment may manage several projects through a
workspace registry. In that case the operator defines the canonical workspace
root, identity marker, registry, and runtime Skill root in its `SOUL.md` using
[`../templates/SOUL.project-context.example.md`](../templates/SOUL.project-context.example.md).

This deployment layer is optional. Repository-local adoption and validation do
not depend on a global registry, a particular home directory, cloud provider,
or private operations repository.

## Acceptance

Before treating a release as adopted:

1. run Context Kit repository validation;
2. validate the generated or migrated project;
3. exercise recovery from `PROJECT.md` through the current pointers;
4. run the consumer's native build/test validation;
5. for multi-repository projects, verify exact component revisions and System
   Task relationships using accessible component roots or reviewed Handoffs.

An inaccessible repository is not checked and must never be reported as
passed.
