# Adoption Guide

Context Kit is a public protocol and reference implementation for
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
  --runtime-adapter codex \
  --workflow-adapter github \
  --dry-run
```

Run the same command without `--dry-run` after the target and profile are
confirmed. Initialization never overwrites a different existing file. Validate
the result:

```sh
python3 scripts/context_kit.py validate --root <target-project>
```

The generated `.context-kit/manifest.json` records the specification version,
Kit release, profile, enabled features, selected runtime adapters, and consumer
extension namespace. Omit `--runtime-adapter` for a neutral CLI-only project;
repeat it only when more than one runtime genuinely shares the project.
Omit `--workflow-adapter` when repository policy supplies the acceptance
boundary without a packaged adapter.

## Choose a profile

| Profile | Includes | Use when |
|---|---|---|
| `minimal` | Identity, adoption metadata, current state | A small or new project does not yet need durable work indexes |
| `repository` | Minimal + Tasks + decisions + context index | A repository needs multi-session maintenance |
| `multi-repo` | Repository + System Task routing + component lock | One integration owner coordinates multiple repositories |

The `repository` and `multi-repo` profiles may enable `checkpoints` or
`memory` with repeatable `--feature` arguments. Do not enable an empty feature
only to populate the tree.

## Adopt an existing project

Audit without mutation:

```sh
python3 scripts/context_kit.py migrate --root <project> --to-spec 2 --check
```

For minimal or repository projects, `--apply` writes the neutral namespace and
then validates existing state. Version 1 `.hermes/` files are retained for
reviewed removal rather than silently deleted. A legacy multi-repository
project requires a reviewed lock/state migration before application; the tool
reports this explicitly rather than discarding its current lock.

See [`UPGRADING.md`](./UPGRADING.md) for version changes and rollback.

## Install Skills

The checkout is the release source; it is not automatically the runtime Skill
directory. Install only the required Skill directories through the consuming
agent runtime's supported Skill mechanism:

| Capability | Skill | Selection |
|---|---|---|
| Durable project context | `project-context-management` | Required for Context Kit operations |
| Advisory AI delivery governance | `ai-delivery-governance` | Optional runtime preparation; actual loading requires explicit project-manifest and current-Task adoption |
| Reusable Skill creation or maintenance | `skill-authoring` | Optional; authoring-time only |
| System Tasks and cross-repository delivery | `multi-repo-system-management` | Required only for multi-repository coordination |

Preserve each runtime directory without flattening it. Record the exact Context
Kit release, distinguish runtime files from source-only validation artifacts,
verify the installed runtime inventory, and keep the previous immutable version
available for rollback. Do not infer a runtime Skill path from a container home
directory or copy Skills into the project root. A runtime adapter must define a
complete installation plan and a verification route; an operator-private
repository must not be required to discover those inputs.

For Hermes, follow the adapter's
[`Skill-first setup`](../adapters/runtime/hermes/README.md#skill-first-setup).
It fixes the solution paths, selects Skills by capability, validates the exact
source revision and split inventories, and installs the complete selection as a
journaled operator transaction. Current Hermes `skill_manage` is not a
supported release transport because it cannot import the immutable checkout
and cannot make a multi-Skill package atomic. Missing host authority is a
specific `Pending user` action, not permission to leave a mixed installation.

## Optional deployment workspace

A long-running runtime may manage several projects through a workspace
registry. Its selected adapter defines the canonical workspace root, identity
marker, registry, Skill root, and any installation-source cache. A checkout
used only as immutable installation source is not a managed project and does
not need a registry row. See the
[`Hermes`](../adapters/runtime/hermes/README.md) and
[`Codex`](../adapters/runtime/codex/README.md) reference adapters.

This deployment layer is optional. Repository-local adoption and validation do
not depend on a global registry, a particular home directory, cloud provider,
or private operations repository.

## Optional runtime instructions

Runtime identity or standing-instruction files are not a prerequisite for
Context Kit. Correctness, safety guards, and lifecycle behavior must remain in
the installed Skills, public adapter contract, or project artifacts.

An adapter may offer an optional reinforcement fragment after Skill
verification. It must show the proposed content and application method, leave
the choice to the user, preserve unrelated existing content, and report a
declined or absent optional fragment without marking runtime adoption
Incomplete. The [Hermes SOUL method](../adapters/runtime/hermes/README.md#optional-soul-reinforcement)
is the reference implementation.

## Acceptance

Before treating a release as adopted:

1. run Context Kit repository validation;
2. validate the generated or migrated project;
3. exercise recovery from `PROJECT.md` through the current pointers;
4. run the consumer's native build/test validation;
5. for multi-repository projects, verify exact component revisions and System
   Task relationships using accessible component roots or reviewed Handoffs.
6. verify each selected runtime adapter's required Skill discovery or runtime
   entry point and one runtime-specific failure path; optional standing
   instructions are verified only when the user chose to apply them.

An inaccessible repository is not checked and must never be reported as
passed.
